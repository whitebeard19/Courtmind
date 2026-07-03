"""
memory_store.py — The ONLY file in this codebase that imports cognee.

This module owns every Cognee Cloud operation:
  remember()  -> ingest + structure into the knowledge graph in one call (queued per case)
  recall()    -> query memory (auto-routes between semantic + graph traversal)
  forget()    -> surgically delete a dataset / case memory
  search()    -> low-level CHUNKS retrieval (used as a resilient recall fallback)

  Note: cognee.improve()/memify() (enrichment) are not enabled on the current tenant, so
  they are not used here (see BUILD_LOG).

Rule: No other file may import cognee. All Cognee calls live here.
"""

import asyncio
import cognee
from cognee import SearchType
from typing import Any

# ---------------------------------------------
# Write-through assertion cache (per-case working set)
# ---------------------------------------------
# Cognee Cloud's search() has a variable eventual-consistency window after cognify(),
# so retrieving freshly-stored assertions for ingest-time contradiction detection is
# unreliable (sometimes returns nothing for several seconds). We keep an in-memory mirror
# of every assertion text we store, keyed by case_id, and use THAT as the contradiction
# candidate pool — instant and 100% reliable in-session. Cognee remains the persistent
# store and powers query/brief/cross-session recall; this is just a fast working set.
_assertion_cache: dict[str, list[str]] = {}


def cache_assertion(case_id: str, text_payload: str) -> None:
    _assertion_cache.setdefault(case_id, []).append(text_payload)


def get_cached_assertions(case_id: str) -> list[dict]:
    """Return cached assertions for a case as candidate dicts ({'text': payload})."""
    return [{"text": t} for t in _assertion_cache.get(case_id, [])]


def clear_cached_assertions(case_id: str) -> None:
    _assertion_cache.pop(case_id, None)


def export_cache() -> dict[str, list[str]]:
    """Snapshot the assertion cache for on-disk persistence (see main.py state file)."""
    return {k: list(v) for k, v in _assertion_cache.items()}


def import_cache(data: dict) -> None:
    """Restore the assertion cache from a persisted snapshot at startup."""
    _assertion_cache.clear()
    if data:
        for k, v in data.items():
            _assertion_cache[k] = list(v)


# ---------------------------------------------
# WRITE — store an assertion into case memory
# ---------------------------------------------

async def store_assertion(case_id: str, assertion: dict, source_doc: str) -> None:
    """
    Store one extracted assertion for a case:
      1. mirror it into the in-memory write-through cache (used for reliable, instant
         contradiction candidates — independent of Cognee latency), and
      2. queue a cognee.remember() write into the case's permanent knowledge graph
         (serialized per case, non-blocking — see schedule_remember / flush_writes).
    """
    text_payload = (
        f"{assertion['text']} "
        f"[Speaker: {assertion.get('speaker') or 'unknown'}] "
        f"[Date: {assertion.get('event_date') or 'unknown'}] "
        f"[Source: {source_doc}]"
    )
    # Cache FIRST so contradiction detection has the assertion regardless of Cognee health.
    # The cache is the authoritative source for real-time contradiction candidates.
    cache_assertion(case_id, text_payload)
    # Persist into Cognee's permanent knowledge graph via remember() (fire-and-forget).
    schedule_remember(case_id, text_payload)


async def store_contradiction(
    case_id: str, assertion_a: str, assertion_b: str,
    reason: str, confidence: float
) -> None:
    """
    Persist a detected contradiction relationship into the case's knowledge graph via a
    queued cognee.remember() write. Storing it as structured text lets Cognee include the
    contradiction in future graph traversals and cross-session recall.
    """
    relationship_text = (
        f"CONTRADICTION: '{assertion_a}' contradicts '{assertion_b}'. "
        f"Reason: {reason}. Confidence: {confidence}."
    )
    # Persist the contradiction relationship into the graph via remember() (queued write).
    schedule_remember(case_id, relationship_text)


# ---------------------------------------------
# Per-case write serialization + flush
# ---------------------------------------------
# remember() persistence is scheduled off the request path so ingest returns fast, BUT:
#   1. writes for a case must be SERIALIZED — concurrent remember() to the same (possibly
#      brand-new) dataset race on dataset creation (observed 409 ProgrammingError) and can
#      produce duplicate/unstable graph state. A per-case lock guarantees one write at a time.
#   2. reads (query/brief) must FLUSH pending writes for the case first, so they never recall
#      a half-written memory. flush_writes() awaits everything queued for the case.
_write_locks: dict[str, asyncio.Lock] = {}
_pending_writes: dict[str, set] = {}


def _write_lock(case_id: str) -> asyncio.Lock:
    lock = _write_locks.get(case_id)
    if lock is None:
        lock = asyncio.Lock()
        _write_locks[case_id] = lock
    return lock


async def _serialized_remember(case_id: str, text: str) -> None:
    async with _write_lock(case_id):
        try:
            await cognee.remember(text, dataset_name=case_id)
        except Exception as e:
            print(f"[WARN] memory_store remember failed (case={case_id}): {e}")


def schedule_remember(case_id: str, text: str) -> None:
    """
    Queue a cognee.remember() write for this case — the flagship ingestion op (ingest +
    permanent graph structuring). Serialized per case (see above) and non-blocking: returns
    immediately so persistence never blocks the ingest response or contradiction detection
    (which reads the in-memory cache). Call flush_writes(case_id) before a read.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    task = loop.create_task(_serialized_remember(case_id, text))
    _pending_writes.setdefault(case_id, set()).add(task)
    task.add_done_callback(lambda t: _pending_writes.get(case_id, set()).discard(t))


async def flush_writes(case_id: str, timeout: float = 90.0) -> None:
    """
    Wait for all pending remember() writes for this case to finish before a read, so
    query/brief always recall a fully-written, consistent case memory. Bounded by `timeout`.
    """
    tasks = list(_pending_writes.get(case_id, set()))
    if not tasks:
        return
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"[WARN] memory_store.flush_writes timed out (case={case_id})")


_bg_build_tasks: set = set()


def schedule_build_graph(case_id: str) -> None:
    """
    Fire-and-forget graph build. Returns immediately so a slow/hanging cognify (e.g. Cognee
    over budget) can NEVER block the ingest response or delay contradiction detection.
    The build runs in the background purely for later query/brief persistence.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # no running loop (e.g. called from sync context) — skip
    task = loop.create_task(build_graph(case_id))
    _bg_build_tasks.add(task)
    task.add_done_callback(_bg_build_tasks.discard)


async def build_graph(case_id: str, timeout: float = 30.0) -> None:
    """
    Build/refresh the knowledge graph for a case from everything staged via add().
    Call ONCE per ingest after all assertions (and again after staging contradictions).

    Best-effort and time-bounded: cognify() is the costly cloud op and can hang or retry
    server-side for minutes when Cognee is unhealthy or its budget is exhausted (observed
    ~275s before a 500). We bound the wait with `timeout` and NEVER raise — graph build is
    only needed for persistence/query/brief, not for contradiction detection (which uses
    the in-memory cache). A failed/timed-out build just means query/brief are degraded
    until Cognee is healthy again.
    """
    # run_in_background=True submits the graph-build job and returns without waiting for the
    # (slow) server-side LLM processing — so a degraded/over-budget Cognee can't stall ingest.
    # wait_for is a secondary bound in case the submit call itself is slow.
    try:
        await asyncio.wait_for(
            cognee.cognify(datasets=[case_id], run_in_background=True),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        print(f"[WARN] memory_store.build_graph submit exceeded {timeout}s (case={case_id}) — continuing")
    except Exception as e:
        print(f"[WARN] memory_store.build_graph (case={case_id}) failed (non-fatal): {e}")


# ---------------------------------------------
# READ — retrieve memory from a case's dataset
# ---------------------------------------------

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


async def recall_chunks(case_id: str, query: str, top_k: int = 10, retries: int = 5) -> list[Any]:
    """
    Raw chunk retrieval — used for brief building and the cross-session contradictions
    fallback. Scoped to THIS case's dataset. Retries on empty results to ride out Cognee
    Cloud's cold-query window; pass retries=1 for a fast, non-blocking single attempt
    (e.g. a GET endpoint that must not hang).
    """
    # Flush pending writes for this case so we never read a half-written memory (unless a
    # fast, non-retry read was explicitly requested — that path also skips the flush wait).
    if retries > 1:
        await flush_writes(case_id)
    try:
        return (await _search_chunks(case_id, query, top_k, retries=retries))[:top_k]
    except Exception as e:
        print(f"[ERROR] memory_store.recall_chunks (case={case_id}, query='{query}'): {e}")
        raise


async def recall_answer(case_id: str, query: str) -> list[Any]:
    """
    User-facing Q&A retrieval via the flagship cognee.recall() — it auto-routes between
    semantic similarity and graph traversal and returns a graph-completion answer that is
    already contradiction-aware. answer_builder.py then frames it with Qwen.

    Robust recovery: flushes pending writes first, then tries recall(); if recall() errors
    OR returns nothing, falls back to a retrying raw CHUNKS search. Only raises if BOTH the
    recall and the search fallback fail — so the caller can fail loudly rather than fake success.
    """
    await flush_writes(case_id)
    try:
        results = await cognee.recall(query_text=query, datasets=[case_id])
        flat = _flatten_search(results)
        if flat:
            return flat
    except Exception as e:
        print(f"[WARN] memory_store.recall_answer recall() failed, falling back to search: {e}")
    # Fallback: retrying raw CHUNKS search. Raises if this also fails (→ HTTP 500 upstream).
    return await _search_chunks(case_id, query, top_k=20)


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


# ---------------------------------------------
# ENRICH — run improve() / memify() for staleness
# ---------------------------------------------

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


# ---------------------------------------------
# DELETE — archive / forget a case's memory
# ---------------------------------------------

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


# ---------------------------------------------
# PIPELINE — full ingest pipeline for one assertion
# ---------------------------------------------

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
