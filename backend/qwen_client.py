"""
qwen_client.py — The ONLY file that makes Qwen API calls.

All Qwen Cloud inference (via DashScope OpenAI-compatible endpoint) lives here.
No other file may call client.chat.completions.create() directly.
"""

import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

# Load .env from project root (courtmind/) and backend dir
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")
load_dotenv()  # also check cwd

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

# Model is env-configurable. Default is qwen-plus (Qwen2.5-based, fast, cheap —
# good for the many pairwise contradiction calls). Set QWEN_MODEL=qwen-max for
# higher reasoning quality. NOTE: the open-source-named "qwen2.5-72b-instruct"
# is NOT enabled on the international (Singapore) endpoint for this account —
# it returns 403. The commercial models qwen-plus / qwen-turbo / qwen-max work.
QWEN_MODEL: str = os.environ.get("QWEN_MODEL", "qwen-plus")


def infer(
    system_prompt: str,
    user_content: str,
    json_mode: bool = False,
    max_tokens: int = 1000,
) -> str:
    """
    Single entry point for all Qwen 2.5-72B inference calls.

    Args:
        system_prompt: The system instruction string.
        user_content: The user message/input string.
        json_mode: If True, requests structured JSON output.
        max_tokens: Output token cap. Bump this for long structured outputs (e.g. the
            trial brief) — the default 1000 can truncate a 500-word brief into invalid JSON.

    Returns:
        Raw string content from the model's response.
    """
    kwargs: dict = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] qwen_client.infer: {e}")
        raise
