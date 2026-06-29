"""
memory_store.py — The ONLY file in this codebase that imports cognee.

This module owns every Cognee Cloud operation:
  remember()  → ingest + graph build in one call
  recall()    → query memory (routes to best strategy automatically)
  forget()    → surgically delete a dataset / case memory
  improve()   → enrichment + staleness pruning (replaces memify)

  Legacy lower-level ops also available via cognee.add() / cognify() / search() / memify()
  if needed for fine-grained control.

Rule: No other file may import cognee. All Cognee calls live here.
"""

import asyncio
import cognee
from cognee import SearchType
from typing import Any

# ─────────────────────────────────────────────
# WRITE — store an assertion into case memory
# ─────────────────────────────────────────────

async def store_assertion(case_id: str, assertion: dict, source_doc: str) -> None:
    """
    Stage one extracted assertion into this case's dataset via cognee.add().

    NOTE: this only ADDS the raw text — it does NOT build the graph. Call build_graph()
    ONCE after staging all of a document's assertions. cognify() is the expensive step
    (~15s/call cloud-side); batching it per-document instead of per-assertion is the
    single biggest ingest-latency win.
    """
    text_payload = (
        f"{assertion['text']} "
        f"[Speaker: {assertion.get('speaker') or 'unknown'}] "
        f"[Date: {assertion.get('event_date') or 'unknown'}] "
        f"[Source: {source_doc}]"
    )
    try:
        await cognee.add(text_payload, dataset_name=case_id)
    except Exception as e:
        print(f"[ERROR] memory_store.store_assertion (case={case_id}): {e}")
        raise


async def store_contradiction(
    case_id: str, assertion_a: str, assertion_b: str,
    reason: str, confidence: float
) -> None:
    """
    Stage a detected contradiction relationship into the case's dataset via cognee.add().
    Like store_assertion(), this does NOT cognify — call build_graph() once afterward.
    Storing as structured text lets Cognee include it in future graph traversals.
    """
    relationship_text = (
        f"CONTRADICTION: '{assertion_a}' contradicts '{assertion_b}'. "
        f"Reason: {reason}. Confidence: {confidence}."
    )
    try:
        await cognee.add(relationship_text, dataset_name=case_id)
    except Exception as e:
        print(f"[ERROR] memory_store.store_contradiction (case={case_id}): {e}")
        raise


async def build_graph(case_id: str) -> None:
    """
    Build/refresh the knowledge graph for a case from everything staged via add().
    Call ONCE per ingest after all assertions (and again after staging contradictions),
    rather than once per assertion. This is the costly cloud operation.
    """
    try:
        await cognee.cognify(datasets=[case_id])
    except Exception as e:
        print(f"[ERROR] memory_store.build_graph (case={case_id}): {e}")
        raise


# ─────────────────────────────────────────────
# READ — retrieve memory from a case's dataset
# ─────────────────────────────────────────────

def _flatten_search(results: list[Any]) -> list[Any]:
    """
    Cognee Cloud's search() wraps results per dataset:
        [{ "dataset_id": ..., "dataset_name": ..., "search_result": [chunk, chunk, ...] }, ...]
    Flatten that into a flat list of the inner chunk dicts (each carries a 'text' field).
    Handles the non-wrapped shape defensively too.
    """
    chunks: list[Any] = []
    for r in results or []:
        if isinstance(r, dict) and "search_result" in r:
            sr = r["search_result"]
            if isinstance(sr, list):
                chunks.extend(sr)
            elif sr is not None:
                chunks.append(sr)
        else:
            chunks.append(r)
    # Cognee Cloud sometimes returns a conversational session reply (a plain string,
    # e.g. "Got it, thanks for the update.") instead of graph chunks — this happens
    # when the query looks like a statement/vague phrase. Real knowledge-graph chunks
    # are dicts carrying a 'text' field. Drop the conversational strings so they never
    # pollute contradiction candidates or answer context. (See BUILD_LOG Session 2.)
    return [c for c in chunks if isinstance(c, dict)]


async def _search_chunks(case_id: str, query: str, top_k: int, retries: int = 5, delay: float = 2.0) -> list[Any]:
    """
    Run a CHUNKS search scoped to the case, retrying while the result is empty.

    Cognee Cloud's search has an eventual-consistency / cold-first-query window: the
    first search (e.g. right after cognify, or the first call after connecting) can
    return 0 results, with the real chunks appearing on a retry a second or two later.
    Without this retry, ingest-time contradiction detection intermittently sees no
    candidates and misses real contradictions. We retry a bounded number of times;
    a genuinely empty dataset just costs a few extra seconds.

    Uses cognee.search(SearchType.CHUNKS), NOT recall() — recall() routes through
    conversational session memory and returns chatty acknowledgements instead of facts.
    """
    last: list[Any] = []
    for attempt in range(retries):
        results = await cognee.search(
            query_text=query,
            query_type=SearchType.CHUNKS,
            datasets=[case_id],
            top_k=top_k,
        )
        last = _flatten_search(results)
        if last:
            return last
        if attempt < retries - 1:
            await asyncio.sleep(delay)
    return last


async def recall_chunks(case_id: str, query: str, top_k: int = 10) -> list[Any]:
    """
    Raw chunk retrieval — used for contradiction-candidate lookup and brief building.
    Scoped to THIS case's dataset so cases never cross-contaminate. Retries on empty
    results to ride out Cognee Cloud's cold-first-query window (see _search_chunks).
    """
    try:
        return (await _search_chunks(case_id, query, top_k))[:top_k]
    except Exception as e:
        print(f"[ERROR] memory_store.recall_chunks (case={case_id}, query='{query}'): {e}")
        raise


async def recall_answer(case_id: str, query: str) -> list[Any]:
    """
    Retrieval for user-facing Q&A and brief generation. Returns the case's stored
    chunks (via search(CHUNKS)) so answer_builder.py / brief_generator.py can feed
    them to Qwen for contradiction-aware synthesis. Uses a wider top_k so any stored
    CONTRADICTION entries are included in the context.
    """
    try:
        return await _search_chunks(case_id, query, top_k=20)
    except Exception as e:
        print(f"[ERROR] memory_store.recall_answer (case={case_id}, query='{query}'): {e}")
        raise


def _extract_text(result: Any) -> str:
    """
    Safely extract text from a Cognee recall result object.
    Handles both dict-style and attribute-style results defensively.
    """
    # cognee v1 recall returns typed entries whose text lives in different fields
    # depending on the entry type:
    #   ResponseGraphEntry        -> .text
    #   ResponseQAEntry           -> .answer
    #   ResponseGraphContextEntry -> .content
    #   ResponseSessionContextEntry -> .content
    if isinstance(result, dict):
        return (
            result.get("text")
            or result.get("answer")
            or result.get("content")
            or result.get("search_result")
            or str(result)
        )
    for attr in ("text", "answer", "content"):
        val = getattr(result, attr, None)
        if val:
            return val
    if hasattr(result, "search_result"):
        sr = result.search_result
        if isinstance(sr, list) and sr:
            return sr[0].get("text", str(sr[0]))
        return str(sr)
    return str(result)


def format_recall_results(results: list[Any]) -> str:
    """Format a list of recall results into a numbered string for Qwen synthesis."""
    lines = []
    for i, r in enumerate(results):
        lines.append(f"[{i+1}] {_extract_text(r)}")
    return "\n".join(lines) if lines else "(No relevant memory found)"


# ─────────────────────────────────────────────
# ENRICH — run improve() / memify() for staleness
# ─────────────────────────────────────────────

async def enrich_and_prune(case_id: str) -> None:
    """
    Run Cognee's enrichment + staleness pruning step.
    Uses cognee.improve() which is the new API equivalent of memify().
    Falls back to memify() if improve() is not available on the connected version.
    """
    try:
        if hasattr(cognee, "improve"):
            await cognee.improve(dataset=case_id)
        elif hasattr(cognee, "memify"):
            await cognee.memify(datasets=[case_id])
        else:
            print(f"[WARN] memory_store.enrich_and_prune: neither improve() nor memify() found on cognee module.")
    except Exception as e:
        print(f"[ERROR] memory_store.enrich_and_prune (case={case_id}): {e}")
        raise


# ─────────────────────────────────────────────
# DELETE — archive / forget a case's memory
# ─────────────────────────────────────────────

async def archive_case(case_id: str) -> None:
    """
    Surgically forget a closed case's dataset from Cognee Cloud memory.
    Uses cognee.forget() — the new API for dataset deletion.
    """
    try:
        if hasattr(cognee, "forget"):
            await cognee.forget(dataset=case_id)
        elif hasattr(cognee, "prune"):
            await cognee.prune.prune_data(dataset_name=case_id)
        else:
            print(f"[WARN] memory_store.archive_case: no supported deletion API found.")
    except Exception as e:
        print(f"[ERROR] memory_store.archive_case (case={case_id}): {e}")
        raise


# ─────────────────────────────────────────────
# PIPELINE — full ingest pipeline for one assertion
# ─────────────────────────────────────────────

async def post_ingest_pipeline(
    case_id: str,
    new_assertion_text: str,
    source_doc: str,
    assertion: dict,
) -> list[dict]:
    """
    Full memory lifecycle for a single ingested assertion:
      1. remember()  → store assertion + build graph
      2. recall()    → fetch contradiction candidates from existing graph
      3. (caller does Qwen contradiction check)
      4. remember()  → store any found contradictions back into graph
      5. improve()   → enrich + prune stale nodes

    Returns the list of contradiction candidates for caller to judge with Qwen.
    This function intentionally returns candidates, not verdicts — contradiction
    judgment is Qwen's job (contradiction_detector.py), not Cognee's.
    """
    # Step 1: store the new assertion
    await store_assertion(case_id, assertion, source_doc)

    # Step 2: recall candidates for contradiction checking
    candidates = await recall_chunks(case_id, new_assertion_text, top_k=10)

    # Step 5 will run after caller does Steps 3-4 (contradiction storage)
    # Return candidates so contradiction_detector.py can judge them with Qwen
    return candidates
