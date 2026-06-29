"""
test_full_pipeline.py — Day 2: Full pipeline test via FastAPI endpoints.

Tests the end-to-end flow:
  1. Create a case
  2. Ingest Test Case 1 document
  3. Ingest Test Case 2 contradicting document
  4. Query the case memory
  5. Get contradictions list
  6. Generate a brief

Run from courtmind/backend/:
  python tests/test_full_pipeline.py

Requires: All API keys in .env + backend running on http://localhost:8000
  Start with: uvicorn main:app --reload
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Run: pip install httpx")
    sys.exit(1)


SEPARATOR = "=" * 60
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")


# ─── Test Data from TEST_CASES.md ───
TC1_DOCUMENT = """I attended the quarterly review meeting on Tuesday, March 12, 2024. The meeting
took place at the downtown office on Fifth Street. I signed the updated vendor
contract at the end of the meeting. Sarah Chen was also present."""

TC2_DOC_A = "The quarterly review meeting took place on Tuesday, March 12, 2024."
TC2_DOC_B = "The quarterly review meeting was held on Thursday, March 14, 2024."


def run_full_pipeline():
    print(SEPARATOR)
    print("CourtMind — Day 2: Full Pipeline Test (via FastAPI)")
    print(f"Backend URL: {BASE_URL}")
    print(SEPARATOR)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    # ─── Step 0: Health check ───
    print(f"\n{'─'*40}")
    print("Step 0: Health check...")
    try:
        r = client.get("/")
        print(f"  ✅ Backend is running: {r.json()}")
    except httpx.ConnectError:
        print(f"  ❌ Cannot connect to {BASE_URL}")
        print(f"     Start the backend first: cd backend && uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False

    # ─── Step 1: Create a case ───
    print(f"\n{'─'*40}")
    print("Step 1: Creating test case...")
    r = client.post("/api/cases", json={"name": "Pipeline Test Alpha", "description": "Automated test case"})
    if r.status_code != 200:
        print(f"  ❌ Create case failed: {r.status_code} {r.text}")
        return False
    case = r.json()
    case_id = case["case_id"]
    print(f"  ✅ Case created: {case_id} ({case['name']})")

    # ─── Step 2: Ingest Test Case 1 (Martinez deposition) ───
    print(f"\n{'─'*40}")
    print("Step 2: Ingesting Test Case 1 (Martinez deposition)...")
    start = time.time()
    r = client.post("/api/ingest", json={
        "case_id": case_id,
        "document_text": TC1_DOCUMENT,
        "source_label": "Martinez Deposition p.1",
        "speaker": "John Martinez",
    })
    elapsed = time.time() - start

    if r.status_code != 200:
        print(f"  ❌ Ingest failed: {r.status_code}")
        print(f"     Response: {r.text[:500]}")
        return False

    result = r.json()
    print(f"  ✅ Ingest completed in {elapsed:.1f}s")
    print(f"     Assertions extracted: {result.get('assertions_extracted', '?')}")
    print(f"     Contradictions found: {result.get('contradictions_found', '?')}")
    if result.get("assertions"):
        for i, a in enumerate(result["assertions"][:5]):
            print(f"     [{i+1}] {a.get('text', '?')[:80]}")

    tc1_passed = result.get("assertions_extracted", 0) >= 3
    print(f"  {'✅' if tc1_passed else '❌'} Test Case 1: {result.get('assertions_extracted', 0)} assertions (expected ≥3)")

    # ─── Step 3: Ingest Test Case 2A (Martinez date claim) ───
    print(f"\n{'─'*40}")
    print("Step 3: Ingesting Test Case 2A (Martinez date claim)...")
    r = client.post("/api/ingest", json={
        "case_id": case_id,
        "document_text": TC2_DOC_A,
        "source_label": "Martinez Deposition p.1",
        "speaker": "John Martinez",
    })
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ Assertions: {result.get('assertions_extracted', '?')}, Contradictions: {result.get('contradictions_found', '?')}")
    else:
        print(f"  ⚠️  Ingest returned {r.status_code}: {r.text[:200]}")

    # ─── Step 4: Ingest Test Case 2B (Chen contradicting date) ───
    print(f"\n{'─'*40}")
    print("Step 4: Ingesting Test Case 2B (Chen's contradicting date)...")
    start = time.time()
    r = client.post("/api/ingest", json={
        "case_id": case_id,
        "document_text": TC2_DOC_B,
        "source_label": "Chen Statement",
        "speaker": "Sarah Chen",
    })
    elapsed = time.time() - start

    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ Ingest completed in {elapsed:.1f}s")
        print(f"     Assertions: {result.get('assertions_extracted', '?')}")
        print(f"     Contradictions: {result.get('contradictions_found', '?')}")
        if result.get("contradictions"):
            for c in result["contradictions"]:
                print(f"     🔴 CONTRADICTION: {c.get('reason', '?')}")
                print(f"        Confidence: {c.get('confidence', '?')}")
        tc2_passed = result.get("contradictions_found", 0) >= 1
        print(f"  {'✅' if tc2_passed else '❌'} Test Case 2: Contradiction {'detected' if tc2_passed else 'NOT detected'}")
    else:
        print(f"  ❌ Ingest failed: {r.status_code}: {r.text[:200]}")
        tc2_passed = False

    # ─── Step 5: Query the case memory ───
    print(f"\n{'─'*40}")
    print("Step 5: Querying 'What did Martinez say about the meeting date?'...")
    start = time.time()
    r = client.post("/api/query", json={
        "case_id": case_id,
        "question": "What did Martinez say about the meeting date?",
    })
    elapsed = time.time() - start

    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ Query completed in {elapsed:.1f}s")
        print(f"     Answer: {result.get('answer', '?')[:300]}")
        print(f"     Sources: {len(result.get('sources', []))} items")
    else:
        print(f"  ❌ Query failed: {r.status_code}: {r.text[:200]}")

    # ─── Step 6: Get contradictions ───
    print(f"\n{'─'*40}")
    print("Step 6: Fetching contradictions list...")
    r = client.get("/api/contradictions", params={"case_id": case_id})
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ Found {len(result.get('contradictions', []))} contradictions")
        for c in result.get("contradictions", []):
            print(f"     • {c.get('assertion_a', '?')[:60]}")
            print(f"       vs {c.get('assertion_b', '?')[:60]}")
            print(f"       Confidence: {c.get('confidence', '?')}")
    else:
        print(f"  ⚠️  Contradictions endpoint: {r.status_code}")

    # ─── Step 7: Generate brief ───
    print(f"\n{'─'*40}")
    print("Step 7: Generating trial brief...")
    start = time.time()
    r = client.post("/api/brief", json={
        "case_id": case_id,
        "case_name": "Pipeline Test Alpha",
        "max_words": 500,
    })
    elapsed = time.time() - start

    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ Brief generated in {elapsed:.1f}s")
        print(f"     Summary: {result.get('brief_summary', '?')[:200]}")
        print(f"     Contradictions: {len(result.get('top_contradictions', []))}")
        print(f"     Key assertions: {len(result.get('key_assertions', []))}")
    else:
        print(f"  ⚠️  Brief generation: {r.status_code}: {r.text[:200]}")

    # ─── Step 8: List cases ───
    print(f"\n{'─'*40}")
    print("Step 8: Listing all cases...")
    r = client.get("/api/cases")
    if r.status_code == 200:
        result = r.json()
        print(f"  ✅ {len(result.get('cases', []))} cases found")
    else:
        print(f"  ⚠️  List cases: {r.status_code}")

    # ─── Summary ───
    print(f"\n{SEPARATOR}")
    print("FULL PIPELINE TEST SUMMARY")
    print(SEPARATOR)
    print(f"  Test Case 1 (Extraction): {'✅ PASS' if tc1_passed else '❌ FAIL'}")
    print(f"  Test Case 2 (Contradiction): {'✅ PASS' if tc2_passed else '❌ FAIL'}")
    print(f"  Query: {'✅ Completed' if r.status_code == 200 else '❌ Failed'}")
    print(SEPARATOR)

    return tc1_passed


if __name__ == "__main__":
    success = run_full_pipeline()
    sys.exit(0 if success else 1)
