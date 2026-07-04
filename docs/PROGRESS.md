# CourtMind — Progress (PROGRESS.md)

**Last updated:** June 29, 2026 — Session 2 (Days 1–3 verified live; contradiction detection working)

---

## Status Summary

| Component | Status | Notes |
|---|---|---|
| `cognee_config.py` | ✅ Complete | Uses `cognee.serve()` — new cloud SDK pattern |
| `memory_store.py` | ✅ Complete | All 4 lifecycle ops + text extraction helper |
| `qwen_client.py` | ✅ Complete | Single inference entry point |
| `prompts.py` | ✅ Complete | All 6 prompts from PROMPTS.md |
| `extractor.py` | ✅ Complete | Assertion extraction |
| `contradiction_detector.py` | ✅ Complete | Full contradiction pass including storage + enrich |
| `answer_builder.py` | ✅ Complete | Q&A synthesis |
| `brief_generator.py` | ✅ Complete | Trial brief generation |
| `langgraph_agent.py` | ✅ Complete | 3-node graph (classify / ingest / query / brief) |
| `main.py` | ✅ Complete | All 7 API routes per API_CONTRACT.md |
| Frontend — `/ingest` | ✅ Complete | Full ingest form with assertion + contradiction display |
| Frontend — `/query` | ✅ Complete | Q&A with source display |
| Frontend — `/contradictions` | ✅ Complete | Contradiction map with confidence bars |
| Frontend — `/brief` | ✅ Complete | Structured trial brief display |
| Frontend — CaseSelector | ✅ Complete | Inline case creation |
| Frontend — api.ts | ✅ Complete | All endpoint calls |
| README.md | ✅ Complete | Submission doc covering all 6 judging criteria |
| .env.example | ✅ Complete | Updated with correct COGNEE_API_KEY + COGNEE_TENANT_URL |
| requirements.txt | ✅ Complete | `cognee` (not `cogwit-sdk`) |

---

## Verified LIVE in Session 2 (June 29)

- ✅ **Day 1** — Qwen Cloud (basic + JSON mode + intent classification) and Cognee Cloud round trip both pass. cognee **1.2.2** confirmed.
- ✅ **Day 1 fix** — `qwen2.5-72b-instruct` is 403-denied on the intl endpoint → switched to **`qwen-plus`** (env-configurable `QWEN_MODEL`).
- ✅ **Day 2** — Extraction (4 assertions) ✅, cross-session query ✅ via `test_full_pipeline.py`.
- ✅ **Day 3** — Contradiction detection **WORKING**: Test Case 2 detected at confidence 1.0. Write path switched to `add()`+`cognify()`; retrieval via `search(CHUNKS)` with topical query + string-result filtering.
- ✅ Fixed memory_store bugs (`improve(dataset=)`, `forget(dataset=)`, dataset-scoped retrieval, `_extract_text`/`_flatten_search`).
- ✅ Python 3.12 venv at `backend/venv/`; `.env` populated; `CACHING=false` set.

## Resolved this session

- ✅ **`GET /api/contradictions`** now reliable (in-memory registry + Cognee fallback) — confirmed 4 contradictions returned.
- ✅ **Brief generation** fixed (max_tokens 3000 + code-fence strip) — confirmed real brief output.
- ✅ **Query answer truncation** fixed (answer max_tokens 1500).
- 🔧 **Ingest latency** refactored to batch cognify/improve once per document (was per-assertion) + skip redundant intent classification on `/api/ingest`. **Pending live wall-clock confirmation after backend restart.**

## Full pipeline — ALL GREEN (confirmed live, June 29)

`test_full_pipeline.py` end to end: extraction ✅, contradiction detection ✅ (conf 1.0), query ✅, `/api/contradictions` ✅ (4), brief ✅, no timeout. Backend is feature-complete for Days 1–3.

**Latency (functional, not snappy):** TC1 ingest ~60s, single-assertion ingest ~40s, brief ~60s. Dominated by per-pair Qwen judgment calls + Cognee cognify/improve + the cold-search retry. Acceptable for a demo if we pre-ingest; the next optimization lever (if needed) is capping/pre-filtering the candidate pool to cut Qwen judgment calls.

## Backend verification — DONE

- ✅ `PATCH /api/cases/{id}/archive` (Cognee `forget`) — works
- ✅ TEST_CASE #5 (cross-session) — fresh process retrieves prior-session memory, sourced + contradiction-aware
- ✅ TEST_CASE #7 (empty/no-contradiction edge) — no false positives, no errors
- ✅ TEST_CASE #6 (brief) — generates valid structured brief
- ⚠️ TEST_CASE #4 (staleness/memify) — `improve()` 404s on fresh datasets; deferred (lowest-priority feature, non-blocking). See BUILD_LOG.

**Backend is verified and ready. Moving to Day 4 (frontend).**

## Session 3 (June 30) — frontend integration hardening

- 🟥 **Cognee Cloud budget exhausted ($2.50 cap)** → `cognify()` 500s and blocks ~275s (the UI "timeout"). **ACTION: user must restore Cognee budget** (promo `COGNEE-35` = $35). Query/brief/persistence are degraded until then.
- ✅ **Contradiction detection decoupled from Cognee** — now uses an in-memory write-through assertion cache + Qwen, so it works even with Cognee down/over-budget. Centerpiece is resilient.
- ✅ `build_graph()` best-effort + 45s timeout (never blocks/aborts ingest); all Cognee ops in `ingest_node` non-fatal.
- ✅ `/api/contradictions` no longer hangs (registry-first; single-attempt Cognee fallback).

## Still pending (Days 4–6)

- [ ] Run the 4 frontend screens against the live backend (Day 4)
- [ ] Run remaining TEST_CASES.md #4, #5, #6, #7 end to end
- [ ] Deploy to Alibaba Cloud ECS (backend) + Vercel (frontend)
- [ ] Record 3-minute demo video
- [ ] Final submission on Devpost (Cognee Jul 5, Qwen Jul 9)

---

## How to Test (run after pasting keys into `.env`)

**All commands run from `courtmind/backend/` using the 3.12 venv.** PowerShell:

```powershell
cd backend
# Day 1 — Qwen connectivity (needs DASHSCOPE_API_KEY)
$env:PYTHONPATH="."; .\venv\Scripts\python.exe tests\test_qwen_basic.py
# Day 1 — Cognee Cloud round trip (needs COGNEE_API_KEY + COGNEE_TENANT_URL)
.\venv\Scripts\python.exe tests\test_cognee_roundtrip.py
# Day 2 — extraction (TEST_CASE 1)
.\venv\Scripts\python.exe tests\test_extractor.py
# Day 2/3 — contradiction detection (TEST_CASES 2 & 3)
.\venv\Scripts\python.exe tests\test_contradiction.py
# Day 2 — full pipeline via API
.\venv\Scripts\python.exe tests\test_full_pipeline.py
# Or run everything in order:
.\venv\Scripts\python.exe tests\run_tests.py
```

To run the live server + frontend:
```powershell
# backend (from backend/)
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
# frontend (from frontend/, separate terminal)
npm install; npm run dev
```

---

## What's Not Yet Built (explicitly deferred)

- Authentication / authorization (explicitly out of scope per HLD)
- PDF/OCR ingestion (text paste only, v1 scope)
- Staleness indicator in UI (deferred until `improve()` return shape confirmed)
- Alibaba Cloud OSS document storage (not required for core demo)
