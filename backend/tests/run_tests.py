"""
run_tests.py — Master test runner for CourtMind Day 1 & Day 2 deliverables.

Usage (from courtmind/backend/):
  python tests/run_tests.py              # Run all tests
  python tests/run_tests.py qwen         # Qwen tests only (Day 1)
  python tests/run_tests.py cognee       # Cognee round trip (Day 1)
  python tests/run_tests.py extractor    # Extractor test (Day 2)
  python tests/run_tests.py contradiction # Contradiction tests (Day 2)
  python tests/run_tests.py pipeline     # Full pipeline via API (Day 2)
"""

import subprocess
import sys
import os
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent

TEST_MAP = {
    "qwen": "test_qwen_basic.py",
    "cognee": "test_cognee_roundtrip.py",
    "extractor": "test_extractor.py",
    "contradiction": "test_contradiction.py",
    "pipeline": "test_full_pipeline.py",
}

SEPARATOR = "=" * 60


def run_test(name: str, filename: str) -> bool:
    print(f"\n{SEPARATOR}")
    print(f"  Running: {name} ({filename})")
    print(SEPARATOR)

    result = subprocess.run(
        [sys.executable, str(TESTS_DIR / filename)],
        cwd=str(BACKEND_DIR),
        env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
    )
    return result.returncode == 0


def main():
    args = sys.argv[1:]

    if args:
        # Run specific tests
        tests_to_run = []
        for arg in args:
            if arg in TEST_MAP:
                tests_to_run.append((arg, TEST_MAP[arg]))
            else:
                print(f"Unknown test: {arg}")
                print(f"Available: {', '.join(TEST_MAP.keys())}")
                sys.exit(1)
    else:
        # Run all tests in order
        tests_to_run = list(TEST_MAP.items())

    print(SEPARATOR)
    print("CourtMind — Test Suite Runner")
    print(f"Tests: {', '.join(name for name, _ in tests_to_run)}")
    print(SEPARATOR)

    results = {}
    for name, filename in tests_to_run:
        results[name] = run_test(name, filename)

    # Summary
    print(f"\n\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")

    all_passed = all(results.values())
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
