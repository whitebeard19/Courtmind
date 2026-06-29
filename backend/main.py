"""
main.py — FastAPI application and route definitions.

Owns: HTTP route definitions ONLY. No business logic here.
All logic delegated to langgraph_agent.py and module functions.

Routes (per API_CONTRACT.md):
  POST   /api/cases
  GET    /api/cases
  POST   /api/ingest
  POST   /api/query
  POST   /api/brief
  GET    /api/contradictions
  PATCH  /api/cases/{case_id}/archive
"""

import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (courtmind/) before any module imports
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")
load_dotenv()  # also check cwd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cognee_config import connect_to_cloud, disconnect_from_cloud
import memory_store
import extractor
import answer_builder
import brief_generator
from langgraph_agent import agent, AgentState


# ─────────────────────────────────────────────────────────────────
# In-memory case registry (no SQL — Cognee owns persistent state)
# This is ephemeral metadata only; actual memory lives in Cognee Cloud.
# ─────────────────────────────────────────────────────────────────
cases: dict[str, dict] = {}

# Per-case contradiction registry. Cognee remains the persistent store, but its
# semantic retrieval of CONTRADICTION records is unreliable, so we also cache every
# contradiction detected during ingest here for a rock-solid /api/contradictions feed.
# Keyed by case_id → list of {assertion_a, assertion_b, reason, confidence}.
contradictions_by_case: dict[str, list[dict]] = {}


def _register_contradictions(case_id: str, found: list[dict]) -> None:
    """Append newly-detected contradictions to the per-case registry, deduped by pair."""
    bucket = contradictions_by_case.setdefault(case_id, [])
    existing = {(c["assertion_a"], c["assertion_b"]) for c in bucket}
    for c in found or []:
        key = (c.get("assertion_a"), c.get("assertion_b"))
        if key not in existing:
            bucket.append(c)
            existing.add(key)


# ─────────────────────────────────────────────────────────────────
# App lifecycle — connect to Cognee Cloud on startup
# ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] main: Connecting to Cognee Cloud...")
    await connect_to_cloud()
    print("[INFO] main: Cognee Cloud connected.")
    yield
    print("[INFO] main: Disconnecting from Cognee Cloud...")
    await disconnect_from_cloud()


app = FastAPI(
    title="CourtMind API",
    description="Legal litigation memory assistant powered by Cognee Cloud + Qwen",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────

class CreateCaseRequest(BaseModel):
    name: str
    description: Optional[str] = None


class IngestRequest(BaseModel):
    case_id: str
    document_text: str
    source_label: str
    speaker: Optional[str] = None


class QueryRequest(BaseModel):
    case_id: str
    question: str


class BriefRequest(BaseModel):
    case_id: str
    case_name: str
    max_words: int = 500


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────

@app.post("/api/cases")
async def create_case(req: CreateCaseRequest) -> dict:
    case_id = str(uuid.uuid4())[:8]  # short, readable ID
    now = datetime.now(timezone.utc).isoformat()
    case = {
        "case_id": case_id,
        "name": req.name,
        "description": req.description,
        "status": "active",
        "created_at": now,
    }
    cases[case_id] = case
    return {
        "case_id": case_id,
        "name": req.name,
        "status": "active",
        "created_at": now,
    }


@app.get("/api/cases")
async def list_cases() -> dict:
    return {"cases": list(cases.values())}


@app.post("/api/ingest")
async def ingest_document(req: IngestRequest) -> dict:
    if not req.document_text:
        raise HTTPException(status_code=400, detail="document_text is required")
    if not req.case_id:
        raise HTTPException(status_code=400, detail="case_id is required")

    state: AgentState = {
        "input": req.document_text,
        "case_id": req.case_id,
        "intent": "ingest",
        "result": {},
        "error": None,
        "source_label": req.source_label,
        "speaker": req.speaker,
    }

    try:
        final_state = await agent.ainvoke(state)
    except Exception as e:
        print(f"[ERROR] main.ingest_document agent invoke: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])

    result = final_state["result"]
    # Cache detected contradictions so /api/contradictions is reliable for the UI.
    _register_contradictions(req.case_id, result.get("contradictions", []))
    return result


@app.post("/api/query")
async def query_case(req: QueryRequest) -> dict:
    if not req.question:
        raise HTTPException(status_code=400, detail="question is required")

    try:
        result = await answer_builder.build_answer(req.case_id, req.question)
        return result
    except Exception as e:
        print(f"[ERROR] main.query_case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/brief")
async def generate_brief(req: BriefRequest) -> dict:
    try:
        result = await brief_generator.generate_brief(
            case_id=req.case_id,
            case_name=req.case_name,
            max_words=req.max_words,
        )
        return result
    except Exception as e:
        print(f"[ERROR] main.generate_brief: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contradictions")
async def get_contradictions(
    case_id: str,
    min_confidence: float = 0.5,
) -> dict:
    """
    Return contradictions for a case. Primary source is the in-memory registry
    populated during ingest (reliable). If that's empty (e.g. a fresh backend process
    in a later session), fall back to parsing CONTRADICTION records out of Cognee memory.
    """
    cached = [
        c for c in contradictions_by_case.get(case_id, [])
        if c.get("confidence", 0) >= min_confidence
    ]
    if cached:
        return {"contradictions": cached}

    # Cross-session fallback: parse stored CONTRADICTION chunks out of Cognee.
    try:
        # Search Cognee for CONTRADICTION entries in this case's memory
        results = await memory_store.recall_chunks(
            case_id, "CONTRADICTION contradicts conflicting statements", top_k=20
        )
        contradiction_texts = [
            memory_store._extract_text(r)
            for r in results
            if "CONTRADICTION" in memory_store._extract_text(r)
        ]

        # Parse stored contradiction strings back into structured form
        # Format: "CONTRADICTION: 'A' contradicts 'B'. Reason: R. Confidence: C."
        parsed: list[dict] = []
        for text in contradiction_texts:
            try:
                parts = text.replace("CONTRADICTION: ", "")
                # Simple parse — robust enough for hackathon demo
                confidence_part = parts.split("Confidence: ")[-1].rstrip(".")
                confidence = float(confidence_part)
                if confidence >= min_confidence:
                    reason_part = parts.split("Reason: ")[-1].split(". Confidence:")[0]
                    main_part = parts.split("'. Reason:")[0]
                    ab = main_part.split("' contradicts '")
                    assertion_a = ab[0].lstrip("'") if len(ab) > 0 else ""
                    assertion_b = ab[1].rstrip("'") if len(ab) > 1 else ""
                    parsed.append({
                        "assertion_a": assertion_a,
                        "assertion_b": assertion_b,
                        "reason": reason_part,
                        "confidence": confidence,
                    })
            except Exception:
                continue  # skip malformed entries

        return {"contradictions": parsed}
    except Exception as e:
        print(f"[ERROR] main.get_contradictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/cases/{case_id}/archive")
async def archive_case(case_id: str) -> dict:
    try:
        await memory_store.archive_case(case_id)
        if case_id in cases:
            cases[case_id]["status"] = "archived"
        contradictions_by_case.pop(case_id, None)
        return {"case_id": case_id, "status": "archived"}
    except Exception as e:
        print(f"[ERROR] main.archive_case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root() -> dict:
    return {
        "name": "CourtMind API",
        "version": "1.0.0",
        "memory_layer": "Cognee Cloud",
        "reasoning_layer": "Qwen 2.5-72B",
        "docs": "/docs",
    }
