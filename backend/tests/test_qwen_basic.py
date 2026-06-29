"""
test_qwen_basic.py — Day 1 deliverable: verify Qwen Cloud connectivity.

Tests:
  1. Basic Qwen inference (plain text response)
  2. JSON mode inference
  3. Intent classification prompt

Run from courtmind/backend/:
  python tests/test_qwen_basic.py

Requires: DASHSCOPE_API_KEY in .env
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


SEPARATOR = "=" * 60


def test_qwen():
    print(SEPARATOR)
    print("CourtMind — Day 1: Qwen Cloud Basic Test")
    print(SEPARATOR)

    # ─── Step 0: Check env ───
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key or api_key == "sk-your-dashscope-key-here":
        print("\n❌ DASHSCOPE_API_KEY not set. Add it to .env:")
        print("   DASHSCOPE_API_KEY=sk-your-real-key-here")
        print("   Get from: https://dashscope-intl.aliyuncs.com")
        return False

    print(f"✅ DASHSCOPE_API_KEY: {api_key[:12]}...")

    # Import after env is loaded
    from qwen_client import infer

    # ─── Test 1: Basic inference ───
    print(f"\n{SEPARATOR}")
    print("Test 1: Basic inference (plain text response)")
    print(SEPARATOR)

    try:
        response = infer(
            system_prompt="You are a helpful assistant. Respond in one sentence.",
            user_content="What is a deposition in legal terms?"
        )
        print(f"✅ Response: {response}")
        print(f"   Length: {len(response)} chars")
    except Exception as e:
        print(f"❌ Basic inference failed: {e}")
        return False

    # ─── Test 2: JSON mode ───
    print(f"\n{SEPARATOR}")
    print("Test 2: JSON mode inference")
    print(SEPARATOR)

    try:
        response = infer(
            system_prompt="Return a JSON object with a single key 'status' and value 'ok'.",
            user_content="Give me the status.",
            json_mode=True
        )
        print(f"✅ Raw response: {response}")
        parsed = json.loads(response)
        print(f"   Parsed: {parsed}")
        assert "status" in parsed, "Expected 'status' key in JSON"
        print(f"   ✅ JSON parsing works correctly")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"   Raw: {response!r}")
        return False
    except Exception as e:
        print(f"❌ JSON mode inference failed: {e}")
        return False

    # ─── Test 3: Intent Classification ───
    print(f"\n{SEPARATOR}")
    print("Test 3: Intent Classification (PROMPT 1)")
    print(SEPARATOR)

    from prompts import INTENT_PROMPT

    test_inputs = [
        ("I attended the quarterly review meeting on Tuesday, March 12, 2024.", "ingest"),
        ("What did Martinez say about the meeting date?", "query"),
        ("Generate a trial prep brief for Case Alpha", "brief"),
    ]

    all_correct = True
    for user_input, expected in test_inputs:
        try:
            response = infer(INTENT_PROMPT, user_input).strip().lower()
            status = "✅" if response == expected else "⚠️"
            if response != expected:
                all_correct = False
            print(f"  {status} Input: \"{user_input[:60]}...\"")
            print(f"     Expected: {expected} | Got: {response}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            all_correct = False

    # ─── Summary ───
    print(f"\n{SEPARATOR}")
    print("✅ Day 1 Qwen Cloud Test Complete!" if all_correct else "⚠️  Some tests had unexpected results (check above)")
    print(SEPARATOR)

    return True


if __name__ == "__main__":
    success = test_qwen()
    sys.exit(0 if success else 1)
