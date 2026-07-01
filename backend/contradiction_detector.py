"""
contradiction_detector.py — Contradiction detection logic.

Owns: querying Cognee for candidates (via memory_store) + Qwen contradiction judgment.
Does NOT call Cognee directly — uses memory_store.py for all memory operations.
Does NOT write contradictions to memory — that's memory_store.store_contradiction().
"""

import re
import json
from qwen_client import infer
from memory_store import (
    recall_chunks, store_contradiction, enrich_and_prune, build_graph, _extract_text,
)
from prompts import CONTRADICTION_PROMPT

CONFIDENCE_THRESHOLD = 0.7

# Strips the "[Speaker: ...] [Date: ...] [Source: ...]" metadata that store_assertion()
# bakes into the stored text. That metadata is ingestion context only — it must never
# appear in the user-facing contradiction card (Bug 3).
_TAG_RE = re.compile(r"\s*\[(?:Speaker|Date|Source):[^\]]*\]")

# If the model's free-text reason concludes the statements are compatible, we must NOT
# store it as a contradiction even if it returned contradicts=true (Bug 2: the reason and
# the boolean disagreeing is the most damaging thing a judge can see).
_HEDGE_PHRASES = (
    "do not contradict", "does not contradict", "not contradict",
    "do not strictly", "does not strictly", "not strictly contradict",
    "can both be true", "could both be true", "both can be true",
    "are compatible", "is compatible", "not a contradiction", "no contradiction",
    "not necessarily contradict", "do not conflict", "does not conflict",
    "sequential events", "different events",
)


def _clean_text(text: str) -> str:
    """Remove ingestion metadata tags from an assertion string for display/comparison."""
    return _TAG_RE.sub("", text or "").strip()


def _reason_supports_contradiction(reason: str) -> bool:
    """True unless the reason text hedges toward 'not a contradiction'."""
    r = (reason or "").lower()
    return not any(h in r for h in _HEDGE_PHRASES)


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

        # Strip ingestion metadata tags so both the Qwen comparison AND the stored/displayed
        # text are clean (Bug 3).
        clean_candidate = _clean_text(candidate_text)
        clean_new = _clean_text(new_assertion_text)

        # Skip if the candidate IS the new assertion (self-comparison)
        if clean_candidate == clean_new:
            continue

        prompt_input = (
            f"Statement A: {clean_new}\n"
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

        reason = result.get("reason", "")
        is_contradiction = (
            result.get("contradicts")
            and result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
            # Guard (Bug 2): drop it if the reason text itself says it's NOT a contradiction.
            and _reason_supports_contradiction(reason)
        )
        if is_contradiction:
            contradictions.append({
                "assertion_a": clean_new,
                "assertion_b": clean_candidate,
                "reason": reason,
                "confidence": result["confidence"],
            })

    return contradictions


def dedupe_contradictions(contradictions: list[dict]) -> list[dict]:
    """
    Collapse near-duplicate contradictions so the UI isn't flooded (Bug 4). When the same
    candidate statement (assertion_b) is flagged by multiple new assertions, keep only the
    single highest-confidence entry. Keyed on the normalized assertion_b text.
    """
    best: dict[str, dict] = {}
    for c in contradictions:
        key = " ".join((c.get("assertion_b") or "").lower().split())
        if key not in best or c.get("confidence", 0) > best[key].get("confidence", 0):
            best[key] = c
    # Preserve highest-confidence-first ordering for the UI.
    return sorted(best.values(), key=lambda c: c.get("confidence", 0), reverse=True)


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
