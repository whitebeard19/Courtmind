"""
test_extractor.py — Day 2 deliverable: verify extractor.py with Test Case 1.

Test Case 1 (from TEST_CASES.md):
  Input: Martinez deposition text
  Expected: 4 distinct assertions with speaker/date tagging

Run from courtmind/backend/:
  python tests/test_extractor.py

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

# ─── Test Case 1 from TEST_CASES.md ───
TEST_CASE_1_INPUT = """I attended the quarterly review meeting on Tuesday, March 12, 2024. The meeting
took place at the downtown office on Fifth Street. I signed the updated vendor
contract at the end of the meeting. Sarah Chen was also present."""

TEST_CASE_1_SOURCE = "Martinez Deposition p.1"
TEST_CASE_1_SPEAKER = "John Martinez"

EXPECTED_FACTS = [
    "attended the quarterly review meeting",
    "March 12, 2024",
    "downtown office",
    "Fifth Street",
    "signed the updated vendor contract",
    "Sarah Chen",
]


def test_extractor():
    print(SEPARATOR)
    print("CourtMind — Day 2: Extractor Test (Test Case 1)")
    print(SEPARATOR)

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key or api_key == "sk-your-dashscope-key-here":
        print("\n❌ DASHSCOPE_API_KEY not set. Add it to .env")
        return False

    print(f"✅ DASHSCOPE_API_KEY: {api_key[:12]}...")

    from extractor import extract_assertions

    # ─── Run extraction ───
    print(f"\n{SEPARATOR}")
    print("Running extractor.extract_assertions()...")
    print(f"  Source: {TEST_CASE_1_SOURCE}")
    print(f"  Speaker: {TEST_CASE_1_SPEAKER}")
    print(f"  Input text ({len(TEST_CASE_1_INPUT)} chars):")
    print(f"  {TEST_CASE_1_INPUT[:200]}...")
    print(SEPARATOR)

    try:
        assertions = extract_assertions(
            document_text=TEST_CASE_1_INPUT,
            source_label=TEST_CASE_1_SOURCE,
            speaker=TEST_CASE_1_SPEAKER,
        )
    except Exception as e:
        print(f"\n❌ extract_assertions() failed: {e}")
        return False

    # ─── Validate results ───
    print(f"\n✅ Extracted {len(assertions)} assertions:")
    print("-" * 40)

    for i, a in enumerate(assertions):
        print(f"\n  [{i+1}] Text: {a.get('text', 'MISSING')}")
        print(f"      Speaker: {a.get('speaker', 'MISSING')}")
        print(f"      Date: {a.get('event_date', 'MISSING')}")
        print(f"      Entities: {a.get('entities', 'MISSING')}")

    # ─── Check pass criteria ───
    print(f"\n{SEPARATOR}")
    print("Pass Criteria Checks:")
    print(SEPARATOR)

    pass_count = 0
    total_checks = 5

    # Check 1: At least 3 assertions (expected 4)
    if len(assertions) >= 3:
        print(f"  ✅ Assertion count: {len(assertions)} (expected ≥3)")
        pass_count += 1
    else:
        print(f"  ❌ Assertion count: {len(assertions)} (expected ≥3)")

    # Check 2: Each assertion has required fields
    all_have_fields = all(
        "text" in a and "speaker" in a for a in assertions
    )
    if all_have_fields:
        print(f"  ✅ All assertions have 'text' and 'speaker' fields")
        pass_count += 1
    else:
        print(f"  ❌ Some assertions missing required fields")

    # Check 3: Speaker tagged correctly
    speaker_tagged = any(
        a.get("speaker") and "Martinez" in str(a.get("speaker", ""))
        for a in assertions
    )
    if speaker_tagged:
        print(f"  ✅ Speaker 'Martinez' correctly tagged in at least one assertion")
        pass_count += 1
    else:
        print(f"  ❌ Speaker 'Martinez' not found in any assertion")

    # Check 4: Date captured
    date_captured = any(
        a.get("event_date") and "2024-03-12" in str(a.get("event_date", ""))
        for a in assertions
    )
    if date_captured:
        print(f"  ✅ Date '2024-03-12' correctly captured")
        pass_count += 1
    else:
        # Check for any date at all
        has_any_date = any(a.get("event_date") for a in assertions)
        if has_any_date:
            dates = [a.get("event_date") for a in assertions if a.get("event_date")]
            print(f"  ⚠️  Date captured but format differs: {dates}")
            pass_count += 0.5
        else:
            print(f"  ❌ No dates captured in any assertion")

    # Check 5: Key facts present
    all_texts = " ".join(a.get("text", "") for a in assertions).lower()
    facts_found = sum(1 for f in EXPECTED_FACTS if f.lower() in all_texts)
    if facts_found >= 4:
        print(f"  ✅ Key facts coverage: {facts_found}/{len(EXPECTED_FACTS)}")
        pass_count += 1
    else:
        print(f"  ⚠️  Key facts coverage: {facts_found}/{len(EXPECTED_FACTS)}")
        pass_count += 0.5

    # ─── Summary ───
    print(f"\n{SEPARATOR}")
    passed = pass_count >= 4
    if passed:
        print(f"✅ TEST CASE 1 PASSED ({pass_count}/{total_checks} checks)")
    else:
        print(f"❌ TEST CASE 1 FAILED ({pass_count}/{total_checks} checks)")
    print(SEPARATOR)

    # ─── Dump raw JSON for reference ───
    print(f"\n--- Raw JSON output (for BUILD_LOG.md) ---")
    print(json.dumps(assertions, indent=2, ensure_ascii=False))

    return passed


if __name__ == "__main__":
    success = test_extractor()
    sys.exit(0 if success else 1)
