"""
answer_builder.py — Answer synthesis from Cognee Cloud recalled memory.

Owns: fetching memory from Cognee + synthesising an answer with Qwen.
No memory writes here — read-only access via memory_store.recall_answer().
"""

from qwen_client import infer
from memory_store import recall_answer, format_recall_results, _extract_text
from prompts import ANSWER_PROMPT


async def build_answer(case_id: str, question: str) -> dict:
    """
    Synthesise a sourced answer to a lawyer's question from Cognee Cloud memory.

    Failure policy (no fake-success): a genuine memory-retrieval or synthesis error RAISES,
    so /api/query returns HTTP 500 rather than a 200 whose body says "Memory retrieval failed".
    An empty case (no memory yet) is NOT an error — it returns a clear, honest 200 message.

    Returns: { "answer": str, "sources": list[str] }
    """
    # recall_answer flushes pending writes, tries recall(), then falls back to CHUNKS search;
    # it only raises if BOTH fail — let that propagate to the route as a real 500.
    graph_results = await recall_answer(case_id, question)

    if not graph_results:
        # Legitimately empty case memory — recover cleanly, don't fake a failure.
        return {
            "answer": "No memory found for this case yet. Ingest one or more documents before asking questions.",
            "sources": [],
        }

    formatted_context = format_recall_results(graph_results)
    source_strings = [_extract_text(r) for r in graph_results]

    user_content = (
        f"Question: {question}\n\n"
        f"Case memory (use only this):\n{formatted_context}\n\n"
        f"Known contradictions:\n(see memory above — any CONTRADICTION entries indicate conflicts)"
    )

    # A Qwen failure here is a real failure — raise so the route returns 500, not a fake 200.
    answer = infer(ANSWER_PROMPT, user_content, json_mode=False, max_tokens=1500)

    return {"answer": answer, "sources": source_strings}
