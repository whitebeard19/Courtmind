"""
answer_builder.py — Answer synthesis from Cognee Cloud recalled memory.

Owns: fetching memory from Cognee + synthesising an answer with Qwen.
No memory writes here — read-only access via memory_store.recall_answer().
"""

from qwen_client import infer
from memory_store import recall_answer, format_recall_results
from prompts import ANSWER_PROMPT


async def build_answer(case_id: str, question: str) -> dict:
    """
    Synthesise a sourced answer to a lawyer's question from Cognee Cloud memory.

    Args:
        case_id: The active case identifier (Cognee dataset_name).
        question: Natural language question from the user.

    Returns:
        { "answer": str, "sources": list[str] }
    """
    try:
        graph_results = await recall_answer(case_id, question)
    except Exception as e:
        print(f"[ERROR] answer_builder.build_answer recall failed: {e}")
        return {"answer": f"Memory retrieval failed: {e}", "sources": []}

    formatted_context = format_recall_results(graph_results)
    # Extract raw source strings for the API response
    source_strings = [formatted_context.split("\n")[i] for i in range(len(graph_results))]

    user_content = (
        f"Question: {question}\n\n"
        f"Case memory (use only this):\n{formatted_context}\n\n"
        f"Known contradictions:\n(see memory above — any CONTRADICTION entries indicate conflicts)"
    )

    try:
        answer = infer(ANSWER_PROMPT, user_content, json_mode=False, max_tokens=1500)
    except Exception as e:
        print(f"[ERROR] answer_builder.build_answer Qwen inference failed: {e}")
        return {"answer": f"Answer synthesis failed: {e}", "sources": source_strings}

    return {
        "answer": answer,
        "sources": source_strings,
    }
