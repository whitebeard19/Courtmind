"""
langgraph_agent.py — LangGraph agent definition, state, and routing.

Owns: agent graph structure, state shape, and routing logic.
Does NOT make direct Qwen or Cognee calls — delegates to qwen_client.py and memory_store.py
via extractor.py, contradiction_detector.py, answer_builder.py, brief_generator.py.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

import qwen_client
import extractor
import memory_store
import answer_builder
import brief_generator
from contradiction_detector import detect_contradictions
from prompts import INTENT_PROMPT


# ─────────────────────────────────────────────────────────────────
# Agent State — the only ephemeral per-request state
# Do not add new fields without updating CONTEXT.md and BUILD_LOG.md.
# ─────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    input: str           # raw user input text
    case_id: str         # active case identifier, doubles as Cognee dataset_name
    intent: str          # "ingest" | "query" | "brief"
    result: dict         # output from whichever node ran
    error: str | None    # error message if any step failed
    # For ingest flows only — set by caller via /api/ingest route args:
    source_label: str    # document label (e.g. 'Martinez Deposition p.1')
    speaker: str | None  # speaker name if known


# ─────────────────────────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────────────────────────

def classify_intent(state: AgentState) -> AgentState:
    """Use Qwen to classify user input as ingest / query / brief.

    If the caller already set a concrete intent (e.g. the /api/ingest route sets
    "ingest"), trust it and skip the extra Qwen call — saves a round trip and removes
    a misclassification risk on the one path that uses this graph.
    """
    if state.get("intent") in ("ingest", "query", "brief"):
        return state
    try:
        raw = qwen_client.infer(INTENT_PROMPT, state["input"])
        intent = raw.strip().lower()
        if intent not in ("ingest", "query", "brief"):
            # Fallback: if model returns garbage, default to query
            intent = "query"
        state["intent"] = intent
    except Exception as e:
        print(f"[ERROR] langgraph_agent.classify_intent: {e}")
        state["intent"] = "query"
        state["error"] = str(e)
    return state


def _pool_query(assertions: list[dict]) -> str:
    """
    Build ONE topical retrieval query for a document by unioning all assertions'
    extracted entities (deduped, order-preserving). A topical noun-phrase query
    reliably returns the case's stored chunks from Cognee; the verbatim sentence does
    not (it triggers a conversational reply). Falls back to the first assertion's text.
    """
    seen: list[str] = []
    for a in assertions:
        for e in (a.get("entities") or []):
            e = str(e).strip()
            if e and e not in seen:
                seen.append(e)
    if seen:
        return " ".join(seen)
    return assertions[0]["text"] if assertions else ""


async def ingest_node(state: AgentState) -> AgentState:
    """
    Full ingest pipeline — structured to call the expensive cloud ops ONCE per document
    instead of once per assertion (the key latency win):
      1. Extract assertions from document text (Qwen)
      2. Stage ALL assertions via add(), then build_graph() ONCE
      3. Recall the candidate pool ONCE (one search for the whole doc, not per assertion)
      4. For each assertion: Qwen contradiction judgment against the shared pool (no writes)
      5. Stage all confirmed contradictions via add(), then build_graph() ONCE
      6. Run improve/memify ONCE for staleness
      7. Return extraction + contradiction counts
    """
    case_id = state["case_id"]
    document_text = state["input"]
    source_label = state.get("source_label", "unknown_document")
    speaker = state.get("speaker")

    try:
        assertions = extractor.extract_assertions(document_text, source_label, speaker)
    except Exception as e:
        print(f"[ERROR] langgraph_agent.ingest_node extract_assertions: {e}")
        state["error"] = str(e)
        state["result"] = {
            "assertions_extracted": 0,
            "contradictions_found": 0,
            "assertions": [],
            "contradictions": [],
        }
        return state

    all_contradictions: list[dict] = []

    try:
        # Step 2: stage every assertion, then build the graph ONCE
        for assertion in assertions:
            await memory_store.store_assertion(case_id, assertion, source_label)
        if assertions:
            await memory_store.build_graph(case_id)

        # Step 3: recall the candidate pool ONCE for the whole document.
        # A single topical query (union of all assertions' entities) returns the case's
        # stored chunks; we reuse this pool for every assertion below. This keeps us to
        # ONE Cognee search per ingest (the search has a costly cold-retry window), instead
        # of one per assertion which previously blew past the request timeout.
        pool_query = _pool_query(assertions)
        candidate_pool: list = []
        if assertions:
            try:
                candidate_pool = await memory_store.recall_chunks(case_id, pool_query, top_k=20)
            except Exception as e:
                print(f"[ERROR] langgraph_agent.ingest_node recall pool: {e}")

        # Step 4: contradiction judgment per assertion against the shared pool (no writes)
        for assertion in assertions:
            try:
                contradictions = await detect_contradictions(
                    case_id, assertion["text"], candidate_pool
                )
                all_contradictions.extend(contradictions)
            except Exception as e:
                print(f"[ERROR] langgraph_agent.ingest_node contradiction check for '{assertion.get('text','')[:60]}': {e}")

        # Step 4: stage all contradictions, then build the graph ONCE
        if all_contradictions:
            for c in all_contradictions:
                await memory_store.store_contradiction(
                    case_id=case_id,
                    assertion_a=c["assertion_a"],
                    assertion_b=c["assertion_b"],
                    reason=c["reason"],
                    confidence=c["confidence"],
                )
            await memory_store.build_graph(case_id)

        # Step 5: enrichment + staleness pruning ONCE
        try:
            await memory_store.enrich_and_prune(case_id)
        except Exception as e:
            print(f"[ERROR] langgraph_agent.ingest_node enrich_and_prune: {e}")

    except Exception as e:
        print(f"[ERROR] langgraph_agent.ingest_node: {e}")
        state["error"] = str(e)

    state["result"] = {
        "assertions_extracted": len(assertions),
        "contradictions_found": len(all_contradictions),
        "assertions": [
            {
                "text": a["text"],
                "speaker": a.get("speaker"),
                "event_date": a.get("event_date"),
            }
            for a in assertions
        ],
        "contradictions": all_contradictions,
    }
    return state


async def query_node(state: AgentState) -> AgentState:
    """Retrieve from Cognee memory and synthesise an answer with Qwen."""
    try:
        result = await answer_builder.build_answer(state["case_id"], state["input"])
        state["result"] = result
    except Exception as e:
        print(f"[ERROR] langgraph_agent.query_node: {e}")
        state["error"] = str(e)
        state["result"] = {"answer": f"Query failed: {e}", "sources": []}
    return state


async def brief_node(state: AgentState) -> AgentState:
    """Generate a trial prep brief from Cognee memory via Qwen."""
    try:
        result = await brief_generator.generate_brief(
            case_id=state["case_id"],
            case_name=state.get("input", state["case_id"]),
            max_words=500,
        )
        state["result"] = result
    except Exception as e:
        print(f"[ERROR] langgraph_agent.brief_node: {e}")
        state["error"] = str(e)
        state["result"] = {}
    return state


# ─────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────

def route(state: AgentState) -> str:
    return state.get("intent", "query")


# ─────────────────────────────────────────────────────────────────
# Graph Definition
# ─────────────────────────────────────────────────────────────────

graph = StateGraph(AgentState)
graph.add_node("classify", classify_intent)
graph.add_node("ingest", ingest_node)
graph.add_node("query", query_node)
graph.add_node("brief", brief_node)

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify",
    route,
    {
        "ingest": "ingest",
        "query": "query",
        "brief": "brief",
    },
)
graph.add_edge("ingest", END)
graph.add_edge("query", END)
graph.add_edge("brief", END)

agent = graph.compile()
