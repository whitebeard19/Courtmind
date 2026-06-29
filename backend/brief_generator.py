"""
brief_generator.py — Trial preparation brief generation.

Owns: fetching case memory from Cognee + generating structured trial briefs with Qwen.
No memory writes here — read-only access via memory_store.recall_chunks().
"""

import json
from qwen_client import infer
from memory_store import recall_chunks, format_recall_results
from prompts import BRIEF_PROMPT


def _strip_code_fences(raw: str) -> str:
    """Defensively strip ```json ... ``` fences a model may wrap JSON in."""
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1] if "\n" in s else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


async def generate_brief(
    case_id: str,
    case_name: str,
    max_words: int = 500,
) -> dict:
    """
    Generate a structured trial preparation brief for a case.

    Fetches contradiction data and key assertions from Cognee Cloud memory,
    then synthesises a structured brief with Qwen.

    Args:
        case_id: The case identifier (Cognee dataset_name).
        case_name: Human-readable case name for the brief header.
        max_words: Word budget for the brief.

    Returns:
        Structured brief dict matching BRIEF_PROMPT schema:
        { top_contradictions, unresolved_questions, key_assertions, brief_summary }
    """
    try:
        contradiction_results = await recall_chunks(
            case_id, "contradictions and conflicting statements", top_k=10
        )
        key_assertion_results = await recall_chunks(
            case_id, "most important case facts key evidence", top_k=10
        )
    except Exception as e:
        print(f"[ERROR] brief_generator.generate_brief recall failed: {e}")
        return {
            "top_contradictions": [],
            "unresolved_questions": [f"Memory retrieval failed: {e}"],
            "key_assertions": [],
            "brief_summary": "Brief generation failed due to a memory retrieval error.",
        }

    formatted_contradictions = format_recall_results(contradiction_results)
    formatted_key_assertions = format_recall_results(key_assertion_results)

    user_input = (
        f"Case name: {case_name}\n\n"
        f"Top contradictions (ranked by confidence):\n{formatted_contradictions}\n\n"
        f"Unresolved assertions (no linked resolution):\n(derive from memory above)\n\n"
        f"Highest confidence assertions:\n{formatted_key_assertions}\n\n"
        f"Word budget: {max_words}"
    )

    try:
        # max_tokens raised well above the default 1000 — a structured 500-word brief
        # (contradictions + questions + assertions + summary) easily exceeds 1000 tokens
        # and truncates into invalid JSON otherwise.
        raw = infer(BRIEF_PROMPT, user_input, json_mode=True, max_tokens=3000)
        brief = json.loads(_strip_code_fences(raw))
        return brief
    except json.JSONDecodeError as e:
        print(f"[ERROR] brief_generator.generate_brief: JSON parse failed: {e}")
        return {
            "top_contradictions": [],
            "unresolved_questions": [],
            "key_assertions": [],
            "brief_summary": "Brief generation failed due to a JSON parsing error.",
        }
    except Exception as e:
        print(f"[ERROR] brief_generator.generate_brief: {e}")
        return {
            "top_contradictions": [],
            "unresolved_questions": [],
            "key_assertions": [],
            "brief_summary": f"Brief generation failed: {e}",
        }
