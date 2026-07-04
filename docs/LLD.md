# CourtMind — Low Level Design (LLD)

**Version:** 4.0 — Cognee (open-source, build now) → Cognee Cloud (migrate later) + Qwen  
**Date:** June 2026  
**Submissions:** Cognee Hackathon "The Hangover Part AI" (Jun 29 – Jul 5, 2026) · Qwen Cloud Hackathon Track 1 (deadline Jul 9, 2026)  
**Target prize:** Best Use of Cognee Cloud (Apple iPhone 17) — **conditional on Cloud signup capacity opening up before submission**

---

## 0. Build Strategy — Open Source Now, Cognee Cloud Later

**Why:** Cognee Cloud (`platform.cognee.ai`) is currently at signup capacity — many hackathon participants, including this team, cannot create an account or get a `COGWIT_API_KEY`. Waiting for this to clear is not a safe plan given the compressed 6-day build window.

**Decision:** Build the entire project now against the **open-source `cognee` pip package** (self-hosted, no signup required, fully documented, works immediately). This is not a workaround or a lesser version — `cognee` and Cognee Cloud's `cogwit-sdk` wrap the **same underlying memory lifecycle** (add → cognify → search → memify). Cognee Cloud is simply the hosted version of this same engine.

**How the migration stays cheap:** every single Cognee call in the entire codebase lives inside one file — `memory_store.py` (see `CONTEXT.md` file ownership rules). No other file ever imports `cognee` or `cogwit_sdk` directly. This means migrating later is rewriting the internals of one file, not the project.

**Migration trigger:** the moment Cognee Cloud signup opens and an API key is obtained, follow this document's migration checklist (Section 10) to swap `memory_store.py`'s internals from `cognee` module calls to `cogwit_instance` client calls, then re-run every scenario in `TEST_CASES.md` to confirm parity before resubmitting README/demo materials naming Cognee Cloud specifically.

**If Cloud access never opens before submission:** submit on open-source `cognee`. This still satisfies the general "Best Use of Cognee" judging criterion and the Open Source prize track. Only the iPhone 17-specific "Best Use of Cognee Cloud" prize becomes unreachable — nothing else about the project, the Qwen submission, or the other 5 judging criteria is affected. State this plainly in the README as a known platform capacity issue during the hackathon window.

---

## 1. Version History

- **v2.0** sketched the open-source `cognee` pip package with module-level calls. Targets the Cognee hackathon's "Best Use of Open Source" prize (MacBook).
- **v3.0** replaced every Cognee touchpoint with `cogwit-sdk` for the hosted Cognee Cloud platform, targeting the iPhone 17 prize — confirmed against `docs.cognee.ai/cognee-cloud/cognee-cloud-sdk`.
- **v4.0 (current)** reverts the *build* to open-source `cognee` because Cognee Cloud signup is currently capacity-blocked, while keeping `cogwit-sdk` as the documented migration target the moment Cloud access opens. See Section 0 above.

| Open-source `cognee` (build now) | Cognee Cloud `cogwit-sdk` (migrate later, if access opens) |
|---|---|
| `pip install cognee` | `pip install cogwit-sdk` |
| `import cognee` then `await cognee.add(...)` (module-level) | `from cogwit_sdk import cogwit, CogwitConfig` then `await cogwit_instance.add(...)` (client instance) |
| Self-hosted vector/graph store (local LanceDB/NetworkX or configured providers); needs an LLM + embedding provider configured (we use Qwen for this) | Fully managed — Postgres + LanceDB + Kuzu on Modal; `COGWIT_API_KEY` from the Cognee Cloud dashboard; no separate embedding config needed |
| Method names: `add()`, `cognify()`, `search()`, `memify()` — same family of calls | Same method *names*, called on a client instance instead of the module: `add()`, `cognify()`, `search()` (with `SearchType.GRAPH_COMPLETION` or `SearchType.CHUNKS`), `memify()` |
| No signup required, works immediately | Requires Cognee Cloud account + API key — currently blocked by signup capacity |

**Why migration is cheap either direction:** the method names and overall lifecycle (add → cognify → search → memify) are the same family of calls in both. The only things that change are the import, the client object, and the auth mechanism. As long as every Cognee call lives inside `memory_store.py` (per `CONTEXT.md`'s file ownership rule), swapping is a contained, single-file change.

**What stays the same regardless of which Cognee variant is active:** `qwen_client.py`, `extractor.py` (prompt logic), `contradiction_detector.py` (prompt logic), `answer_builder.py` (prompt logic), `brief_generator.py` (prompt logic), `langgraph_agent.py` (structure), all frontend components, all prompts in PROMPTS.md.

---

## 2. Cognee Setup — Open Source (build now)

### 2.1 Installation

```bash
pip install cognee
```

### 2.2 Configuration

Open-source `cognee` needs an LLM provider and embedding provider configured, since (unlike Cognee Cloud) it doesn't manage this for you. We configure it to use Qwen Cloud (DashScope, OpenAI-compatible) for both, keeping a single AI provider across the whole stack.

```python
# cognee_config.py
import cognee
import os

cognee.config.set_llm_config({
    "llm_provider": "openai",  # Qwen is OpenAI-compatible
    "llm_model": "qwen2.5-72b-instruct",
    "llm_api_key": os.environ["DASHSCOPE_API_KEY"],
    "llm_endpoint": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
})

cognee.config.set_embedding_config({
    "embedding_provider": "openai",
    "embedding_model": "text-embedding-v3",
    "embedding_api_key": os.environ["DASHSCOPE_API_KEY"],
    "embedding_endpoint": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "embedding_dimensions": 1024
})

# Vector store and graph store — use cognee's defaults (typically LanceDB +
# NetworkX/Kuzu) for hackathon simplicity unless a specific need arises.
```

**Day 1 build task:** verify these exact config keys against the installed `cognee` version's actual API (`pip show cognee`, then check `cognee.config`'s real method signatures) — treat this as a starting point, not gospel, until tested.

### 2.3 Datasets as Cases

One `cognee` dataset per legal case. `dataset_name` is set to the case's `case_id` throughout the codebase.

```python
await cognee.add(document_text, dataset_name=case_id)
await cognee.cognify(datasets=[case_id])     # builds/updates the knowledge graph
results = await cognee.search(query_text=question, dataset_name=case_id)
```

**Day 1 build task:** confirm the exact `cognify()` and `search()` signatures for the installed open-source version — open-source `cognee`'s API has had naming differences across versions (e.g. `datasets` vs `dataset_ids`, `query_text` vs `query`). Log the confirmed signatures in `BUILD_LOG.md` immediately.

---

## 2A. Cognee Cloud Setup — Migration Target (use once signup access opens)

Keep this section as the reference for the swap. Do not build against this until `COGWIT_API_KEY` is actually obtained.

### Installation
```bash
pip install cogwit-sdk
```

### Account and API Key
1. Sign up at `https://platform.cognee.ai/sign-in`
2. Claim the free Developer plan using code `COGNEE-35` ($35 value)
3. Navigate to the API keys subpage (via the side-menu) inside Cognee Cloud
4. Create an API key, store it as `COGWIT_API_KEY` in `.env`

### Client Setup — confirmed pattern from official docs
```python
# cognee_config.py — Cognee Cloud variant
import os
from cogwit_sdk import cogwit, CogwitConfig

cogwit_config = CogwitConfig(
    api_key=os.environ["COGWIT_API_KEY"],
)

cogwit_instance = cogwit(cogwit_config)
```

This single `cogwit_instance` replaces the module-level `cognee.xxx()` calls. There is no separate LLM/embedding provider configuration needed — Cognee Cloud manages this internally (backed by managed Postgres, LanceDB, and Kuzu, running on Modal).

### Datasets as Cases (Cloud variant)
```python
result = await cogwit_instance.add(data=document_text, dataset_name=case_id)
dataset_id = result.dataset_id   # save this — needed for cognify()

cognify_result = await cogwit_instance.cognify(dataset_ids=[dataset_id])
# wait for PipelineRunCompleted before searching — confirm polling behaviour once accessible
```

---

## 3. Module Breakdown

### 3.1 `qwen_client.py` — unchanged

Single entry point for all Qwen Cloud inference calls.

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

def infer(system_prompt: str, user_content: str, json_mode: bool = False) -> str:
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    response = client.chat.completions.create(
        model="qwen2.5-72b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        max_tokens=1000,
        **kwargs
    )
    return response.choices[0].message.content
```

---

### 3.2 `extractor.py` — unchanged logic, prompt from PROMPTS.md

```python
import json
from qwen_client import infer
from prompts import EXTRACTION_PROMPT

def extract_assertions(document_text: str, source_label: str, speaker: str = None) -> list[dict]:
    user_input = f"Document source: {source_label}\nSpeaker (if known): {speaker}\n\nText:\n{document_text}"
    raw = infer(EXTRACTION_PROMPT, user_input, json_mode=True)
    return json.loads(raw)["assertions"]
```

---

### 3.3 `memory_store.py` — open-source `cognee` (build now), structured for easy Cognee Cloud migration

All Cognee interactions go through this single module — this is the ONLY file in the entire codebase that imports `cognee`. This isolation is what makes the later migration to `cogwit-sdk` a single-file change.

```python
import cognee
from cognee_config import case_dataset_ids  # simple dict tracking case_id -> dataset_id, see note below

async def store_assertion(case_id: str, assertion: dict, source_doc: str) -> None:
    """Push one extracted assertion into cognee's memory for this case's dataset."""
    text_payload = (
        f"{assertion['text']} "
        f"[Speaker: {assertion.get('speaker', 'unknown')}] "
        f"[Date: {assertion.get('event_date', 'unknown')}] "
        f"[Source: {source_doc}]"
    )
    await cognee.add(text_payload, dataset_name=case_id)

async def build_graph(case_id: str):
    """Trigger cognify — builds/updates the knowledge graph for this case's dataset."""
    result = await cognee.cognify(datasets=[case_id])
    return result

async def recall_chunks(case_id: str, query: str, top_k: int = 10) -> list[dict]:
    """Raw chunk-style retrieval — used for contradiction-candidate lookup."""
    results = await cognee.search(query_text=query, dataset_name=case_id)
    return results[:top_k]

async def recall_answer(case_id: str, query: str) -> str:
    """Reasoned retrieval — used for user-facing Q&A and brief generation.
    Open-source cognee's search() may not have distinct query_type modes the
    way cogwit-sdk does (GRAPH_COMPLETION vs CHUNKS) — confirm on Day 1
    whether a query_type parameter exists and use it if so; otherwise the
    same search() call serves both recall_chunks and recall_answer for now,
    with answer_builder.py doing the reasoning Qwen-side instead."""
    results = await cognee.search(query_text=query, dataset_name=case_id)
    return results

async def enrich_and_prune(case_id: str):
    """Run cognee's memify step — enrichment + stale node flagging."""
    result = await cognee.memify(datasets=[case_id])
    return result

async def archive_case(case_id: str):
    """Remove a closed case's dataset from active memory."""
    await cognee.prune.prune_data(dataset_name=case_id)
    # confirm exact deletion API on Day 1 — open-source cognee's deletion/
    # pruning interface may differ from this; check installed version's docs
```

**`cognee_config.py` for the open-source build** just needs the LLM/embedding config from Section 2.2 above — there is no `cogwit_instance` client object to set up in this variant, since open-source `cognee`'s functions are module-level, not called on a client instance.

**Day 1 verification needed (open-source `cognee`):**
- Confirm `cognify()`'s exact parameter name — `datasets` vs `dataset_ids` vs something else — against the installed version.
- Confirm `search()`'s exact signature and return shape, and whether a `query_type` parameter exists for distinguishing chunk-style vs reasoned retrieval.
- Confirm `memify()`'s exact invocation and what it returns/changes.
- Confirm the correct dataset deletion/pruning call.
- Log all of the above in `BUILD_LOG.md` before relying on them elsewhere.

---

### 3.3A `memory_store.py` — Cognee Cloud (`cogwit-sdk`) migration target

Keep as reference for the swap once Cognee Cloud signup access opens. This is the SAME file, SAME function signatures (`store_assertion`, `build_graph`, `recall_chunks`, `recall_answer`, `enrich_and_prune`, `archive_case`) — only the internals change. Every other file in the codebase that imports from `memory_store.py` requires zero changes during this migration.

```python
from cognee_config import cogwit_instance

async def store_assertion(case_id: str, assertion: dict, source_doc: str) -> str:
    text_payload = (
        f"{assertion['text']} "
        f"[Speaker: {assertion.get('speaker', 'unknown')}] "
        f"[Date: {assertion.get('event_date', 'unknown')}] "
        f"[Source: {source_doc}]"
    )
    result = await cogwit_instance.add(data=text_payload, dataset_name=case_id)
    return result.dataset_id  # NOTE: now also need to track dataset_id alongside case_id

async def build_graph(dataset_id: str):
    cognify_result = await cogwit_instance.cognify(dataset_ids=[dataset_id])
    return cognify_result

async def recall_chunks(case_id: str, query: str, top_k: int = 10) -> list[dict]:
    results = await cogwit_instance.search(
        query_text=query,
        query_type=cogwit_instance.SearchType.CHUNKS,
    )
    return results[:top_k]

async def recall_answer(case_id: str, query: str) -> str:
    results = await cogwit_instance.search(
        query_text=query,
        query_type=cogwit_instance.SearchType.GRAPH_COMPLETION,
    )
    return results

async def enrich_and_prune(dataset_id: str):
    result = await cogwit_instance.memify(dataset_ids=[dataset_id])
    return result

async def archive_case(case_id: str, dataset_id: str):
    await cogwit_instance.delete_dataset(dataset_id=dataset_id)
```

**Migration day verification needed:**
- Confirm `search()`'s exact return shape for both `CHUNKS` and `GRAPH_COMPLETION` query types (the official example shows `result.search_result` and `result.search_result[0]['text']` for chunks — confirm against the live SDK).
- Confirm whether `memify()` is exposed as a top-level `cogwit_instance.memify()` method or requires a different call pattern.
- Confirm the exact dataset deletion method name (`delete_dataset`, `forget`, or similar).
- Note the one structural difference: Cognee Cloud's `add()` returns a `dataset_id` that must be tracked alongside `case_id` for later `cognify()`/deletion calls, whereas open-source `cognee` doesn't require this — update `langgraph_agent.py` and any caller of these functions accordingly if migrating.

---

### 3.4 `contradiction_detector.py` — same prompt, queries cognee for candidates

```python
import json
from qwen_client import infer
from memory_store import recall_chunks
from prompts import CONTRADICTION_PROMPT

async def detect_contradictions(case_id: str, new_assertion_text: str) -> list[dict]:
    candidates = await recall_chunks(case_id, new_assertion_text, top_k=10)
    contradictions = []
    for candidate in candidates:
        # exact shape of each `candidate` depends on the confirmed search()
        # return format for the installed cognee version — adjust this
        # extraction once confirmed on Day 1, log the real shape in BUILD_LOG.md
        candidate_text = candidate.get("text") if isinstance(candidate, dict) else str(candidate)
        prompt_input = f"Statement A: {new_assertion_text}\nStatement B: {candidate_text}"
        result = json.loads(infer(CONTRADICTION_PROMPT, prompt_input, json_mode=True))
        if result["contradicts"] and result["confidence"] >= 0.7:
            contradictions.append({
                "candidate_text": candidate_text,
                "reason": result["reason"],
                "confidence": result["confidence"]
            })
    return contradictions
```

When a contradiction is found, store it back into the same case's dataset as additional structured data so the graph reflects it:

```python
import cognee

async def store_contradiction(case_id: str, assertion_a: str, assertion_b: str, reason: str, confidence: float):
    relationship_text = (
        f"CONTRADICTION: '{assertion_a}' contradicts '{assertion_b}'. "
        f"Reason: {reason}. Confidence: {confidence}."
    )
    await cognee.add(relationship_text, dataset_name=case_id)
    await cognee.cognify(datasets=[case_id])
```

---

### 3.5 Staleness via `memify()` — replaces any hand-written staleness scorer

Staleness is delegated to `cognee`'s `memify()` step, explicitly described as enrichment plus stale-node pruning. Qwen still contributes judgment by ensuring contradiction relationships are written into the graph before `memify()` runs, giving it the signal it needs.

```python
async def post_ingest_pipeline(case_id: str, new_assertion_text: str, source_doc: str, assertion: dict):
    await store_assertion(case_id, assertion, source_doc)
    await build_graph(case_id)

    contradictions = await detect_contradictions(case_id, new_assertion_text)
    for c in contradictions:
        await store_contradiction(
            case_id, new_assertion_text, c["candidate_text"],
            c["reason"], c["confidence"]
        )

    await enrich_and_prune(case_id)  # memify() — handles staleness
    return contradictions
```

**Build-week task:** verify what `memify()` actually changes or returns — confirm whether it flags/deprioritises nodes (which CourtMind needs, so stale memories stay visible with an indicator) versus deleting them outright.

**Migration note:** when swapping to `cogwit-sdk` (Section 3.3A), this function needs to track and pass `dataset_id` (returned by Cognee Cloud's `add()`) instead of relying on `case_id` alone — see the migration checklist in Section 9.

---

### 3.6 `answer_builder.py` — same prompt, built from cognee search results

```python
from qwen_client import infer
from memory_store import recall_answer
from prompts import ANSWER_PROMPT

async def build_answer(case_id: str, question: str) -> dict:
    graph_results = await recall_answer(case_id, question)

    formatted_context = "\n".join(
        f"[{i+1}] {r}" for i, r in enumerate(graph_results)
    )

    answer = infer(
        ANSWER_PROMPT,
        f"Question: {question}\n\nCase memory:\n{formatted_context}",
        json_mode=False
    )
    return {"answer": answer, "sources": graph_results}
```

---

### 3.7 `brief_generator.py` — same prompt, sourced from cognee search

```python
import json
from qwen_client import infer
from memory_store import recall_chunks
from prompts import BRIEF_PROMPT

async def generate_brief(case_id: str, case_name: str, max_words: int = 500) -> dict:
    contradictions = await recall_chunks(case_id, "contradictions and conflicting statements", top_k=10)
    key_assertions = await recall_chunks(case_id, "most important case facts", top_k=10)

    user_input = (
        f"Case name: {case_name}\n"
        f"Top contradictions:\n{contradictions}\n\n"
        f"Key assertions:\n{key_assertions}\n\n"
        f"Word budget: {max_words}"
    )
    raw = infer(BRIEF_PROMPT, user_input, json_mode=True)
    return json.loads(raw)
```

---

### 3.8 `langgraph_agent.py` — structure unchanged, calls updated modules

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
import qwen_client, extractor, memory_store, answer_builder

class AgentState(TypedDict):
    input: str
    case_id: str
    intent: Literal["ingest", "query", "brief"]
    result: dict

def classify_intent(state: AgentState) -> AgentState:
    raw = qwen_client.infer(
        "Classify as exactly one word: ingest, query, or brief.",
        state["input"]
    )
    state["intent"] = raw.strip().lower()
    return state

async def ingest_node(state: AgentState) -> AgentState:
    assertions = extractor.extract_assertions(state["input"], source_label="user_upload")
    contradiction_summary = []
    for a in assertions:
        contradictions = await memory_store.post_ingest_pipeline(
            state["case_id"], a["text"], "user_upload", a
        )
        contradiction_summary.extend(contradictions)
    state["result"] = {
        "assertions_stored": len(assertions),
        "contradictions_found": len(contradiction_summary)
    }
    return state

async def query_node(state: AgentState) -> AgentState:
    state["result"] = await answer_builder.build_answer(state["case_id"], state["input"])
    return state

def route(state: AgentState) -> str:
    return state["intent"]

graph = StateGraph(AgentState)
graph.add_node("classify", classify_intent)
graph.add_node("ingest", ingest_node)
graph.add_node("query", query_node)
graph.set_entry_point("classify")
graph.add_conditional_edges("classify", route, {
    "ingest": "ingest",
    "query": "query",
    "brief": END  # handled via separate /api/brief route
})
graph.add_edge("ingest", END)
graph.add_edge("query", END)
agent = graph.compile()
```

---

## 4. API Endpoints

### 4.1 `POST /api/ingest`

**Request:**
```json
{
  "case_id": "string",
  "document_text": "string",
  "source_label": "Witness A deposition - 2024-03-15",
  "speaker": "John Martinez"
}
```

**Response:**
```json
{
  "assertions_extracted": 7,
  "contradictions_found": 2,
  "contradictions": [
    { "assertion_a": "...", "assertion_b": "...", "reason": "...", "confidence": 0.91 }
  ]
}
```

**Processing:** `extractor.extract_assertions()` → loop → `memory_store.post_ingest_pipeline()` (cognee `add` + `cognify` + `search` for candidates + contradiction detection + `add`/`cognify` again + `memify`)

---

### 4.2 `POST /api/query`

**Request:** `{ "case_id": "string", "question": "What did Martinez say about the meeting date?" }`

**Response:**
```json
{
  "answer": "string",
  "sources": [ "..." ]
}
```

**Processing:** `answer_builder.build_answer()` → cognee `search()` → Qwen synthesis

---

### 4.3 `POST /api/brief`

**Request:** `{ "case_id": "string", "case_name": "string", "max_words": 500 }`

**Response:** Structured JSON per `BRIEF_PROMPT` schema in PROMPTS.md

**Processing:** `brief_generator.generate_brief()` → two `search()`(CHUNKS) calls → Qwen brief synthesis

---

### 4.4 `PATCH /api/cases/:id/archive`

**Processing:** `memory_store.archive_case()` → cognee dataset deletion/pruning (open-source) — becomes Cognee Cloud dataset deletion after migration

**Response:** `{ "status": "archived" }`

---

## 5. Frontend Component Map (unchanged)

```
/app
  layout.tsx          → Global navbar with case selector
  /ingest/page.tsx     → DocumentIngestForm
  /query/page.tsx      → QueryInput + AssertionResultList + ContradictionBadge
  /contradictions/page.tsx → ContradictionList + ConfidenceBar
  /brief/page.tsx      → GenerateBriefButton + BriefDisplay

/components
  CaseSelector.tsx
  AssertionCard.tsx
  ContradictionCard.tsx
  StalenessBadge.tsx   → reflects memify() output once its real behaviour is confirmed

/lib
  api.ts
```

---

## 6. Environment Variables

```bash
# Backend (.env)
DASHSCOPE_API_KEY=sk-...          # Qwen Cloud — used by qwen_client.py AND cognee_config.py (LLM/embedding provider for open-source cognee)

# ADD this when migrating to Cognee Cloud (cogwit-sdk):
# COGWIT_API_KEY=...              # Cognee Cloud — used by cognee_config.py / memory_store.py once migrated

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://<ECS_IP>:8000
```

---

## 7. Folder Structure

```
courtmind/
├── backend/
│   ├── main.py                    # FastAPI app, route definitions
│   ├── langgraph_agent.py
│   ├── qwen_client.py
│   ├── cognee_config.py           # cognee LLM/embedding config (open-source) — becomes cogwit_instance setup after migration
│   ├── memory_store.py            # ALL cognee add/cognify/search/memify/delete calls live here — only file that imports cognee
│   ├── extractor.py
│   ├── contradiction_detector.py
│   ├── answer_builder.py
│   ├── brief_generator.py
│   ├── prompts.py                 # Loads prompt strings from PROMPTS.md content
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/api.ts
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   ├── PROMPTS.md
│   ├── CONTEXT.md
│   ├── API_CONTRACT.md
│   ├── BUILD_LOG.md
│   ├── TEST_CASES.md
│   ├── PROGRESS.md
│   └── Roadmap.md
├── .env.example
├── README.md
└── LICENSE                        # MIT
```

---

## 8. Sequence Diagram — Ingest (open-source `cognee`, current build)

```
User → POST /api/ingest
  → FastAPI → LangGraph.classify_intent
  → ingest_node
    → Qwen2.5-72B: extract assertions (JSON)
    → for each assertion:
        → cognee.add(text, dataset_name=case_id)
        → cognee.cognify(datasets=[case_id])
        → cognee.search(text, dataset_name=case_id) → candidate assertions
        → Qwen2.5-72B: detect contradictions among candidates
        → cognee.add(contradiction_relationship, dataset_name=case_id)
        → cognee.cognify(datasets=[case_id])
    → cognee.memify(datasets=[case_id])   # enrichment + staleness pass
  → return { assertions_extracted, contradictions_found }
```

**Migration target — same flow on Cognee Cloud (once `cogwit-sdk` access opens):**
```
    → for each assertion:
        → cogwit.add(text, dataset_name=case_id) → dataset_id
        → cogwit.cognify(dataset_ids=[dataset_id])
        → cogwit.search(text, query_type=CHUNKS) → candidate assertions
        → Qwen2.5-72B: detect contradictions among candidates
        → cogwit.add(contradiction_relationship, dataset_name=case_id)
        → cogwit.cognify(dataset_ids=[dataset_id])
    → cogwit.memify(dataset_ids=[dataset_id])
```

---

## 9. Open Items to Resolve on Day 1 of Build (Jun 29)

**Open-source `cognee` (build now):**
1. Confirm `cognify()`'s exact parameter name (`datasets` vs `dataset_ids`) against the installed version.
2. Confirm `search()`'s exact signature and return object shape — adjust `memory_store.py` and `contradiction_detector.py` parsing accordingly.
3. Confirm `memify()`'s exact invocation and what it returns/changes (flagging vs deletion).
4. Confirm the correct dataset deletion/pruning call for the archive flow.
5. Confirm whether `cognify()` blocks until completion or needs a polling step.

**Cognee Cloud migration (resolve only once signup access opens):**
6. Confirm `search()`'s exact return shape for both `CHUNKS` and `GRAPH_COMPLETION` query types on `cogwit-sdk`.
7. Confirm whether `cogwit_instance.memify()` exists as shown, or requires a different invocation.
8. Confirm the exact dataset-deletion method name (`delete_dataset` or similar) on `cogwit-sdk`.
9. Confirm whether Cognee Cloud's `cognify()` blocks or needs polling for `PipelineRunCompleted` status.
10. Confirm the `$35` `COGNEE-35` Developer plan's actual usage limits against expected build-week + demo load.

---

## 10. Migration Checklist — Open Source → Cognee Cloud

Run this checklist the moment `COGWIT_API_KEY` is obtained:

1. Resolve open items 6–10 above with one real round trip against `cogwit-sdk`.
2. Rewrite `cognee_config.py` per Section 2A (client instance instead of module config).
3. Rewrite `memory_store.py`'s internals per Section 3.3A — function names and signatures stay the same except `store_assertion`/`build_graph`/`archive_case` now also thread a `dataset_id` (see migration note in Section 3.5).
4. Update the two callers that pass `dataset_id` downstream: `post_ingest_pipeline()` in `memory_store.py` and `store_contradiction()` in `contradiction_detector.py`.
5. Re-run all 7 scenarios in `TEST_CASES.md` end to end — confirm identical pass/fail results to the open-source version.
6. Update `.env` / `.env.example` to add `COGWIT_API_KEY` and remove reliance on `cognee.config.set_llm_config()`.
7. Update README and demo materials to explicitly name "Cognee Cloud" and show the platform dashboard as proof — required for "Best Use of Cognee Cloud" judging.
8. Log the completed migration in `BUILD_LOG.md` with the date.

If this checklist cannot be completed before the Cognee Hackathon submission deadline, submit on open-source `cognee` instead — see Section 0 above.

---

*Document owner: CourtMind Team · Cognee submission: Jul 5, 2026 · Qwen submission: Jul 9, 2026*
