"""
test_full_pipeline.py - Day 2: Full pipeline test via FastAPI endpoints.

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
    print("[FAIL] httpx not installed. Run: pip install httpx")
    sys.exit(1)


SEPARATOR = "=" * 60
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")


TC1_DOCUMENT = """I attended the quarterly review meeting on Tuesday, March 12, 2024. The meeting
took place at the downtown office on Fifth Street. I signed the updated vendor
contract at the end of the meeting. Sarah Chen was also present."""

TC2_DOC_A = "The quarterly review meeting took place on Tuesday, March 12, 2024."
TC2_DOC_B = "The quarterly review meeting was held on Thursday, March 14, 2024."


def _query_looks_valid(result: dict) -> tuple[bool, str]:
    """
    Treat query as passing only when it returns substantive memory-backed output.

    A 200 response alone is not enough: the API may return
    "Memory retrieval failed: ..." in the answer body while still using HTTP 200.
    """
    answer = str(result.get("answer", "")).strip()
    sources = result.get("sources", [])

    if not answer:
        return False, "answer was empty"
    if answer.lower().startswith("memory retrieval failed"):
        return False, "answer reported memory retrieval failure"
    if answer.lower().startswith("answer synthesis failed"):
        return False, "answer reported synthesis failure"
    if not isinstance(sources, list) or len(sources) == 0:
        return False, "no source chunks returned"
    return True, "ok"


def run_full_pipeline():
    print(SEPARATOR)
    print("CourtMind - Day 2: Full Pipeline Test (via FastAPI)")
    print(f"Backend URL: {BASE_URL}")
    print(SEPARATOR)

    client = httpx.Client(base_url=BASE_URL, timeout=120.0)

    print(f"\n{'-' * 40}")
    print("Step 0: Health check...")
    try:
        health = client.get("/")
        print(f"  [OK] Backend is running: {health.json()}")
    except httpx.ConnectError:
        print(f"  [FAIL] Cannot connect to {BASE_URL}")
        print("     Start the backend first: cd backend && uvicorn main:app --reload")
        return False
    except Exception as exc:
        print(f"  [FAIL] Health check failed: {exc}")
        return False

    print(f"\n{'-' * 40}")
    print("Step 1: Creating test case...")
    create_case = client.post(
        "/api/cases",
        json={"name": "Pipeline Test Alpha", "description": "Automated test case"},
    )
    if create_case.status_code != 200:
        print(f"  [FAIL] Create case failed: {create_case.status_code} {create_case.text}")
        return False
    case = create_case.json()
    case_id = case["case_id"]
    print(f"  [OK] Case created: {case_id} ({case['name']})")

    print(f"\n{'-' * 40}")
    print("Step 2: Ingesting Test Case 1 (Martinez deposition)...")
    start = time.time()
    ingest1 = client.post(
        "/api/ingest",
        json={
            "case_id": case_id,
            "document_text": TC1_DOCUMENT,
            "source_label": "Martinez Deposition p.1",
            "speaker": "John Martinez",
        },
    )
    elapsed = time.time() - start

    if ingest1.status_code != 200:
        print(f"  [FAIL] Ingest failed: {ingest1.status_code}")
        print(f"     Response: {ingest1.text[:500]}")
        return False

    result = ingest1.json()
    print(f"  [OK] Ingest completed in {elapsed:.1f}s")
    print(f"     Assertions extracted: {result.get('assertions_extracted', '?')}")
    print(f"     Contradictions found: {result.get('contradictions_found', '?')}")
    if result.get("assertions"):
        for i, assertion in enumerate(result["assertions"][:5]):
            print(f"     [{i + 1}] {assertion.get('text', '?')[:80]}")

    tc1_passed = result.get("assertions_extracted", 0) >= 3
    print(
        f"  {'[OK]' if tc1_passed else '[FAIL]'} Test Case 1: "
        f"{result.get('assertions_extracted', 0)} assertions (expected >=3)"
    )

    print(f"\n{'-' * 40}")
    print("Step 3: Ingesting Test Case 2A (Martinez date claim)...")
    ingest2a = client.post(
        "/api/ingest",
        json={
            "case_id": case_id,
            "document_text": TC2_DOC_A,
            "source_label": "Martinez Deposition p.1",
            "speaker": "John Martinez",
        },
    )
    if ingest2a.status_code == 200:
        result = ingest2a.json()
        print(
            f"  [OK] Assertions: {result.get('assertions_extracted', '?')}, "
            f"Contradictions: {result.get('contradictions_found', '?')}"
        )
    else:
        print(f"  [WARN] Ingest returned {ingest2a.status_code}: {ingest2a.text[:200]}")

    print(f"\n{'-' * 40}")
    print("Step 4: Ingesting Test Case 2B (Chen's contradicting date)...")
    start = time.time()
    ingest2b = client.post(
        "/api/ingest",
        json={
            "case_id": case_id,
            "document_text": TC2_DOC_B,
            "source_label": "Chen Statement",
            "speaker": "Sarah Chen",
        },
    )
    elapsed = time.time() - start

    if ingest2b.status_code == 200:
        result = ingest2b.json()
        print(f"  [OK] Ingest completed in {elapsed:.1f}s")
        print(f"     Assertions: {result.get('assertions_extracted', '?')}")
        print(f"     Contradictions: {result.get('contradictions_found', '?')}")
        if result.get("contradictions"):
            for contradiction in result["contradictions"]:
                print(f"     [CONTRADICTION] {contradiction.get('reason', '?')}")
                print(f"        Confidence: {contradiction.get('confidence', '?')}")
        tc2_passed = result.get("contradictions_found", 0) >= 1
        print(
            f"  {'[OK]' if tc2_passed else '[FAIL]'} Test Case 2: "
            f"Contradiction {'detected' if tc2_passed else 'NOT detected'}"
        )
    else:
        print(f"  [FAIL] Ingest failed: {ingest2b.status_code}: {ingest2b.text[:200]}")
        tc2_passed = False

    print(f"\n{'-' * 40}")
    print("Step 5: Querying 'What did Martinez say about the meeting date?'...")
    start = time.time()
    query_response = client.post(
        "/api/query",
        json={
            "case_id": case_id,
            "question": "What did Martinez say about the meeting date?",
        },
    )
    elapsed = time.time() - start

    query_passed = False
    if query_response.status_code == 200:
        result = query_response.json()
        query_passed, query_reason = _query_looks_valid(result)
        print(f"  [OK] Query completed in {elapsed:.1f}s")
        print(f"     Answer: {result.get('answer', '?')[:300]}")
        print(f"     Sources: {len(result.get('sources', []))} items")
        print(f"  {'[OK]' if query_passed else '[FAIL]'} Query validation: {query_reason}")
    else:
        print(f"  [FAIL] Query failed: {query_response.status_code}: {query_response.text[:200]}")

    print(f"\n{'-' * 40}")
    print("Step 6: Fetching contradictions list...")
    contradictions_response = client.get("/api/contradictions", params={"case_id": case_id})
    if contradictions_response.status_code == 200:
        result = contradictions_response.json()
        print(f"  [OK] Found {len(result.get('contradictions', []))} contradictions")
        for contradiction in result.get("contradictions", []):
            print(f"     - {contradiction.get('assertion_a', '?')[:60]}")
            print(f"       vs {contradiction.get('assertion_b', '?')[:60]}")
            print(f"       Confidence: {contradiction.get('confidence', '?')}")
    else:
        print(f"  [WARN] Contradictions endpoint: {contradictions_response.status_code}")

    print(f"\n{'-' * 40}")
    print("Step 7: Generating trial brief...")
    start = time.time()
    brief_response = client.post(
        "/api/brief",
        json={
            "case_id": case_id,
            "case_name": "Pipeline Test Alpha",
            "max_words": 500,
        },
    )
    elapsed = time.time() - start

    if brief_response.status_code == 200:
        result = brief_response.json()
        print(f"  [OK] Brief generated in {elapsed:.1f}s")
        print(f"     Summary: {result.get('brief_summary', '?')[:200]}")
        print(f"     Contradictions: {len(result.get('top_contradictions', []))}")
        print(f"     Key assertions: {len(result.get('key_assertions', []))}")
    else:
        print(f"  [WARN] Brief generation: {brief_response.status_code}: {brief_response.text[:200]}")

    print(f"\n{'-' * 40}")
    print("Step 8: Listing all cases...")
    list_cases_response = client.get("/api/cases")
    if list_cases_response.status_code == 200:
        result = list_cases_response.json()
        print(f"  [OK] {len(result.get('cases', []))} cases found")
    else:
        print(f"  [WARN] List cases: {list_cases_response.status_code}")

    print(f"\n{SEPARATOR}")
    print("FULL PIPELINE TEST SUMMARY")
    print(SEPARATOR)
    print(f"  Test Case 1 (Extraction): {'[PASS]' if tc1_passed else '[FAIL]'}")
    print(f"  Test Case 2 (Contradiction): {'[PASS]' if tc2_passed else '[FAIL]'}")
    print(f"  Query: {'[PASS]' if query_passed else '[FAIL]'}")
    print(SEPARATOR)

    return tc1_passed and tc2_passed and query_passed


if __name__ == "__main__":
    success = run_full_pipeline()
    sys.exit(0 if success else 1)