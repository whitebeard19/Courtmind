"""
contradiction_detector.py — Contradiction detection logic.

Owns: querying Cognee for candidates (via memory_store) + Qwen contradiction judgment.
Does NOT call Cognee directly — uses memory_store.py for all memory operations.
Does NOT write contradictions to memory — that's memory_store.store_contradiction().
"""

import json
from qwen_client import infer
from memory_store import (
    recall_chunks, store_contradiction, enrich_and_prune, build_graph, _extract_text,
)
from prompts import CONTRADICTION_PROMPT

CONFIDENCE_THRESHOLD = 0.7


async def detect_contradictions(
    case_id: str,
    new_assertion_text: str,
    candidates: list,
) -> list[dict]:
    """
    Given a new assertion and a list of existing memory chunks (candidates from Cognee),
    use Qwen to determine which candidates contradict the new assertion.

    Args:
        case_id: The case identifier (also the Cognee dataset_name).
        new_assertion_text: The newly extracted assertion text to check.
        candidates: List of existing memory results from memory_store.recall_chunks().

    Returns:
        List of contradiction dicts above the confidence threshold:
          [{ "assertion_a": str, "assertion_b": str, "reason": str, "confidence": float }]
    """
    contradictions: list[dict] = []

    for candidate in candidates:
        candidate_text = _extract_text(candidate)

        # Skip trivially short or empty candidates
        if not candidate_text or len(candidate_text.strip()) < 10:
            continue

        # Strip metadata from candidate_text for Qwen comparison
        # Metadata is always appended as " [Speaker: "
        clean_candidate = candidate_text
        if " [Speaker: " in clean_candidate:
            clean_candidate = clean_candidate.split(" [Speaker: ")[0].strip()

        # Skip if the candidate IS the new assertion (self-comparison)
        if clean_candidate == new_assertion_text.strip():
            continue

        prompt_input = (
            f"Statement A: {new_assertion_text}\n"
            f"Statement B: {clean_candidate}"
        )

        try:
            raw = infer(CONTRADICTION_PROMPT, prompt_input, json_mode=True)
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[ERROR] contradiction_detector: JSON parse failed: {e}")
            continue
        except Exception as e:
            print(f"[ERROR] contradiction_detector.detect_contradictions: {e}")
            continue

        if result.get("contradicts") and result.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
            contradictions.append({
                "assertion_a": new_assertion_text,
                "assertion_b": candidate_text,
                "reason": result["reason"],
                "confidence": result["confidence"],
            })

    return contradictions


def _topical_query(new_assertion_text: str, assertion: dict) -> str:
    """
    Build a TOPICAL retrieval query (entities/keywords) rather than passing the
    verbatim assertion sentence. Cognee Cloud's search returns a conversational
    reply instead of real chunks when the query is a full statement; a topical
    noun-phrase query reliably returns the stored facts. Falls back to the raw
    text if no entities were extracted.
    """
    entities = assertion.get("entities") or []
    parts = [str(e) for e in entities if e]
    query = " ".join(parts).strip()
    return query or new_assertion_text


async def find_contradictions(
    case_id: str,
    new_assertion_text: str,
    assertion: dict,
) -> list[dict]:
    """
    Side-effect-free contradiction check for one assertion:
      1. Recall candidates from Cognee via a topical query
      2. Qwen judges each candidate pair
    Returns confirmed contradictions above threshold. Does NOT write to memory or
    run enrichment — the caller batches storage/build_graph/improve once per ingest
    (see langgraph_agent.ingest_node) to keep ingest latency low.
    """
    candidates = await recall_chunks(
        case_id, _topical_query(new_assertion_text, assertion), top_k=10
    )
    return await detect_contradictions(case_id, new_assertion_text, candidates)


async def run_full_contradiction_pass(
    case_id: str,
    new_assertion_text: str,
    source_doc: str,
    assertion: dict,
) -> list[dict]:
    """
    Self-contained contradiction pipeline for ONE assertion (used by standalone scripts
    /tests). The API ingest path uses find_contradictions() + batched storage instead.
      1. find_contradictions (recall + Qwen judgment)
      2. Stage confirmed contradictions (add) and build the graph once
      3. Run enrich_and_prune (improve/memify) for staleness handling
    """
    contradictions = await find_contradictions(case_id, new_assertion_text, assertion)

    if contradictions:
        for c in contradictions:
            try:
                await store_contradiction(
                    case_id=case_id,
                    assertion_a=c["assertion_a"],
                    assertion_b=c["assertion_b"],
                    reason=c["reason"],
                    confidence=c["confidence"],
                )
            except Exception as e:
                print(f"[ERROR] contradiction_detector: failed to store contradiction: {e}")
        try:
            await build_graph(case_id)
        except Exception as e:
            print(f"[ERROR] contradiction_detector: build_graph failed: {e}")

    try:
        await enrich_and_prune(case_id)
    except Exception as e:
        print(f"[ERROR] contradiction_detector: enrich_and_prune failed: {e}")

    return contradictions
