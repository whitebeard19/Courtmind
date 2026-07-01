"""
cognee_config.py — Cognee Cloud connection setup.

Uses the NEW Cognee Cloud SDK pattern:
  - pip install cognee  (same package, not cogwit-sdk)
  - cognee.serve(url=..., api_key=...) routes all calls to your cloud tenant
  - Operations: remember(), recall(), forget(), improve() (new API)
  - Fallback: add(), cognify(), search(), memify() also available

Docs: https://docs.cognee.ai/cognee-cloud/connections/cloud-sdk
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (courtmind/) and backend dir — BEFORE importing cognee.
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")
load_dotenv()  # also check cwd

# CRITICAL: disable cognee's conversational SESSION MEMORY (on by default in 1.x).
# CourtMind uses cognee purely as a document knowledge graph. With session memory on,
# remember()/recall()/search() return chatty acknowledgements ("Got it, thank you...")
# instead of the stored assertions — which silently breaks contradiction detection.
# Must be set BEFORE `import cognee`. .env may override via CACHING=...
os.environ.setdefault("CACHING", "false")

import cognee  # noqa: E402  (imported after CACHING is set)

# .strip() guards against stray whitespace in .env (e.g. "COGNEE_TENANT_URL= https://...")
# which would otherwise produce an invalid URL and fail the connection.
COGNEE_API_KEY: str = os.environ["COGNEE_API_KEY"].strip()
COGNEE_TENANT_URL: str = os.environ["COGNEE_TENANT_URL"].strip()  # e.g. https://your-tenant.aws.cognee.ai


async def connect_to_cloud() -> None:
    """Connect the cognee SDK to Cognee Cloud. Call once at app startup."""
    await cognee.serve(
        url=COGNEE_TENANT_URL,
        api_key=COGNEE_API_KEY,
    )


async def disconnect_from_cloud() -> None:
    """Gracefully disconnect from Cognee Cloud. Call at app shutdown."""
    await cognee.disconnect()
