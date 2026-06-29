"""
test_cognee_roundtrip.py — Day 1 deliverable: verify Cognee Cloud connectivity.

Tests the full lifecycle:
  1. cognee.serve() — connect to Cognee Cloud
  2. cognee.remember() — store one sentence
  3. cognee.recall() — retrieve it back
  4. Prints raw return objects so we can confirm their real shape
  5. cognee.forget() — clean up test data (optional)

Run from courtmind/backend/:
  python tests/test_cognee_roundtrip.py

Requires: COGNEE_API_KEY and COGNEE_TENANT_URL in .env (project root or backend dir)
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load .env from project root (courtmind/)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Also try backend dir
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


SEPARATOR = "=" * 60


async def test_roundtrip():
    print(SEPARATOR)
    print("CourtMind — Day 1: Cognee Cloud Round Trip Test")
    print(SEPARATOR)

    # ─── Step 0: Check env vars ───
    api_key = os.environ.get("COGNEE_API_KEY", "")
    tenant_url = os.environ.get("COGNEE_TENANT_URL", "")

    if not api_key or api_key == "your-cognee-cloud-api-key-here":
        print("\n❌ COGNEE_API_KEY not set. Add it to .env:")
        print("   COGNEE_API_KEY=your-real-key-here")
        print("   Get one from: https://platform.cognee.ai → API Keys")
        return False

    if not tenant_url or "your-tenant" in tenant_url:
        print("\n❌ COGNEE_TENANT_URL not set. Add it to .env:")
        print("   COGNEE_TENANT_URL=https://your-tenant.aws.cognee.ai")
        print("   Get your URL from the Cognee Cloud dashboard")
        return False

    print(f"✅ COGNEE_API_KEY: {api_key[:8]}...")
    print(f"✅ COGNEE_TENANT_URL: {tenant_url}")

    # ─── Step 1: Connect to Cognee Cloud ───
    print(f"\n{SEPARATOR}")
    print("Step 1: Connecting to Cognee Cloud via cognee.serve()...")
    print(SEPARATOR)

    import cognee

    try:
        result = await cognee.serve(url=tenant_url, api_key=api_key)
        print(f"✅ cognee.serve() returned: {result}")
        print(f"   Type: {type(result)}")
    except Exception as e:
        print(f"❌ cognee.serve() failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

    # ─── Step 2: Store a test sentence ───
    print(f"\n{SEPARATOR}")
    print("Step 2: Storing test sentence via cognee.remember()...")
    print(SEPARATOR)

    test_text = "John Martinez attended the quarterly review meeting on Tuesday, March 12, 2024 at the downtown office."
    test_dataset = "courtmind_test_roundtrip"

    try:
        remember_result = await cognee.remember(test_text, dataset_name=test_dataset)
        print(f"✅ cognee.remember() returned: {remember_result}")
        print(f"   Type: {type(remember_result)}")
        if hasattr(remember_result, '__dict__'):
            print(f"   Attributes: {vars(remember_result)}")
    except TypeError as e:
        # The API may not accept dataset_name as a keyword
        print(f"⚠️  cognee.remember(text, dataset_name=...) failed: {e}")
        print("   Trying without dataset_name...")
        try:
            remember_result = await cognee.remember(test_text)
            print(f"✅ cognee.remember(text) returned: {remember_result}")
            print(f"   Type: {type(remember_result)}")
        except Exception as e2:
            print(f"❌ cognee.remember() failed: {e2}")
            return False
    except Exception as e:
        print(f"❌ cognee.remember() failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Try fallback: add() + cognify()
        print("\n   Trying fallback: cognee.add() + cognee.cognify()...")
        try:
            add_result = await cognee.add(test_text, dataset_name=test_dataset)
            print(f"   ✅ cognee.add() returned: {add_result}")
            print(f"      Type: {type(add_result)}")

            cognify_result = await cognee.cognify()
            print(f"   ✅ cognee.cognify() returned: {cognify_result}")
            print(f"      Type: {type(cognify_result)}")
        except Exception as e2:
            print(f"   ❌ Fallback add+cognify also failed: {e2}")
            return False

    # ─── Step 3: Wait a moment for processing ───
    print(f"\n{SEPARATOR}")
    print("Step 3: Waiting 3 seconds for graph build to complete...")
    print(SEPARATOR)
    await asyncio.sleep(3)

    # ─── Step 4: Recall the test sentence ───
    print(f"\n{SEPARATOR}")
    print("Step 4: Retrieving via cognee.recall()...")
    print(SEPARATOR)

    test_query = "What meeting did Martinez attend?"

    try:
        recall_result = await cognee.recall(query_text=test_query)
        print(f"✅ cognee.recall() returned: {recall_result}")
        print(f"   Type: {type(recall_result)}")
        print(f"   Length: {len(recall_result) if hasattr(recall_result, '__len__') else 'N/A'}")

        if isinstance(recall_result, list):
            for i, item in enumerate(recall_result[:5]):  # show first 5
                print(f"\n   --- Result [{i}] ---")
                print(f"   Type: {type(item)}")
                print(f"   Value: {item}")
                if isinstance(item, dict):
                    print(f"   Keys: {list(item.keys())}")
                elif hasattr(item, '__dict__'):
                    print(f"   Attributes: {vars(item)}")
                if hasattr(item, 'text'):
                    print(f"   .text: {item.text}")
                if hasattr(item, 'search_result'):
                    print(f"   .search_result: {item.search_result}")
    except TypeError as e:
        print(f"⚠️  cognee.recall(query_text=...) failed: {e}")
        print("   Trying cognee.search()...")
        try:
            search_result = await cognee.search(query_text=test_query)
            print(f"✅ cognee.search() returned: {search_result}")
            print(f"   Type: {type(search_result)}")
        except Exception as e2:
            print(f"❌ Both recall and search failed: {e2}")
            return False
    except Exception as e:
        print(f"❌ cognee.recall() failed: {e}")
        print(f"   Error type: {type(e).__name__}")

        # Try fallback: search()
        print("\n   Trying fallback: cognee.search()...")
        try:
            from cognee.api.v1.search import SearchType
            search_chunks = await cognee.search(SearchType.CHUNKS, query_text=test_query)
            print(f"   ✅ search(CHUNKS) returned: {search_chunks}")
            search_graph = await cognee.search(SearchType.GRAPH_COMPLETION, query_text=test_query)
            print(f"   ✅ search(GRAPH_COMPLETION) returned: {search_graph}")
        except Exception as e2:
            print(f"   ❌ Fallback search also failed: {e2}")
            return False

    # ─── Step 5: Cleanup (optional) ───
    print(f"\n{SEPARATOR}")
    print("Step 5: Cleanup — removing test data...")
    print(SEPARATOR)

    try:
        if hasattr(cognee, 'forget'):
            forget_result = await cognee.forget(dataset=test_dataset)
            print(f"✅ cognee.forget() returned: {forget_result}")
        elif hasattr(cognee, 'prune'):
            prune_result = await cognee.prune.prune_data(dataset_name=test_dataset)
            print(f"✅ cognee.prune.prune_data() returned: {prune_result}")
        else:
            print("⚠️  No forget/prune method found — skipping cleanup")
    except Exception as e:
        print(f"⚠️  Cleanup failed (non-critical): {e}")

    # ─── Step 6: Test improve/memify ───
    print(f"\n{SEPARATOR}")
    print("Step 6: Testing improve/memify availability...")
    print(SEPARATOR)

    print(f"   cognee.improve exists: {hasattr(cognee, 'improve')}")
    print(f"   cognee.memify exists: {hasattr(cognee, 'memify')}")
    print(f"   cognee.remember exists: {hasattr(cognee, 'remember')}")
    print(f"   cognee.recall exists: {hasattr(cognee, 'recall')}")
    print(f"   cognee.forget exists: {hasattr(cognee, 'forget')}")
    print(f"   cognee.serve exists: {hasattr(cognee, 'serve')}")
    print(f"   cognee.add exists: {hasattr(cognee, 'add')}")
    print(f"   cognee.cognify exists: {hasattr(cognee, 'cognify')}")
    print(f"   cognee.search exists: {hasattr(cognee, 'search')}")

    # List all public methods for discovery
    public_methods = [m for m in dir(cognee) if not m.startswith('_')]
    print(f"\n   All public cognee methods: {public_methods}")

    print(f"\n{SEPARATOR}")
    print("✅ Day 1 Cognee Round Trip Test Complete!")
    print("   → Log the results in BUILD_LOG.md")
    print(SEPARATOR)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_roundtrip())
    sys.exit(0 if success else 1)
