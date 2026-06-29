"""
extractor.py — Legal document assertion extraction.

Owns ONLY assertion extraction logic.
No memory calls here — pass extracted assertions to memory_store.py.
"""

import json
from qwen_client import infer
from prompts import EXTRACTION_PROMPT


def extract_assertions(
    document_text: str,
    source_label: str,
    speaker: str | None = None,
) -> list[dict]:
    """
    Extract structured factual assertions from a legal document.

    Args:
        document_text: Raw text of the legal document.
        source_label: Human-readable label for the source (e.g. 'Martinez Deposition p.1').
        speaker: Name of the speaking party if known (e.g. 'John Martinez').

    Returns:
        List of assertion dicts:
          [{ "text": str, "speaker": str|None, "event_date": str|None, "entities": list[str] }]
    """
    user_input = (
        f"Document source: {source_label}\n"
        f"Speaker (if known): {speaker or 'unknown'}\n\n"
        f"Text:\n{document_text}"
    )

    try:
        raw = infer(EXTRACTION_PROMPT, user_input, json_mode=True)
        parsed = json.loads(raw)
        assertions = parsed.get("assertions", [])
        return assertions
    except json.JSONDecodeError as e:
        print(f"[ERROR] extractor.extract_assertions: JSON parse failed: {e}")
        print(f"[ERROR] extractor.extract_assertions: raw response was: {raw!r}")
        raise
    except Exception as e:
        print(f"[ERROR] extractor.extract_assertions: {e}")
        raise
