# CourtMind ⚖
### AI-Powered Litigation Memory Assistant

> **Cognee Hackathon "The Hangover Part AI" submission — WeMakeDevs / Jun 29 – Jul 5 2026**

**AI Assistant Disclosure:** This project was planned and implemented with the assistance of Claude (Anthropic). Per Cognee Hackathon Rule 8, this is disclosed explicitly.

---

## The Problem

Litigation is one of the most memory-intensive professions on earth. A litigator juggling multiple cases reads thousands of pages of depositions, interviews dozens of witnesses, and must track across months — who said what, who contradicted whom, and which exhibit proves which point.

Today this is done with sticky notes and human memory. **A single missed contradiction can lose a case.** No tool connects legal knowledge across sessions automatically.

---

## The Solution

CourtMind gives lawyers a **persistent, cross-session AI memory** for every case. Ingest any legal document — deposition, witness statement, email, contract — and CourtMind:

1. **Extracts** every factual assertion (via Qwen 2.5-72B)
2. **Stores** it in a persistent knowledge graph (via Cognee Cloud)
3. **Detects contradictions** against all prior memory (Qwen judgment over Cognee recall)
4. **Prunes stale information** as new facts supersede old ones (Cognee improve/memify)
5. **Answers questions** with sourced, contradiction-aware answers
6. **Generates trial briefs** from the full case memory

Memory survives across sessions, restarts, and days — because it lives in **Cognee Cloud**, not in-process state.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│          Next.js 14 Frontend                 │
│  /ingest · /query · /contradictions · /brief │
└───────────────┬──────────────────────────────┘
                │ HTTP / REST
┌───────────────▼──────────────────────────────┐
│   LangGraph Agent (Python / FastAPI)         │
│  classify_intent → ingest / query / brief    │
└──────────────┬────────────────────────────────┘
               │
   ┌───────────┴────────────┐
   ▼                        ▼
Qwen 2.5-72B          Cognee Cloud
(DashScope)           (memory layer)
                       ├── remember()   ← ingest + graph build
                       ├── recall()     ← search (auto-routed)
                       ├── improve()    ← staleness pruning
                       └── forget()     ← case archive / deletion
```

**Cognee Cloud** owns all persistent state — backed by managed PostgreSQL, LanceDB, and Kuzu on Modal. One dataset per legal case (`dataset_name = case_id`). **Qwen 2.5-72B** provides all reasoning. **LangGraph** orchestrates routing. **No other database or storage layer exists** — Cognee is the system of record.

---

## How CourtMind Uses Cognee

CourtMind demonstrates the **complete Cognee memory lifecycle** across all four stages:

| Cognee Operation | CourtMind Usage |
|---|---|
| `cognee.remember()` | Ingests each extracted assertion + contradiction relationship into the knowledge graph. Called once per assertion (ingest + graph build in one call). |
| `cognee.recall()` | Two distinct retrieval contexts: (1) contradiction-candidate lookup during ingestion, (2) user-facing Q&A and brief generation |
| `cognee.improve()` | Post-ingestion enrichment + stale node pruning — called after every new assertion and its contradictions are stored |
| `cognee.forget()` | Surgically removes a closed case's dataset from Cognee Cloud memory when archived |

All Cognee calls are isolated in **`memory_store.py`** — the only file in the codebase that imports `cognee`. This maintains a clean separation: Cognee handles memory, Qwen handles reasoning.

---

## Judging Criteria

### 01 Potential Impact
Legal contradiction detection across sessions solves a real, painful problem that directly affects case outcomes. Litigators currently rely on manual review and human memory — both highly fallible. CourtMind replaces this with persistent AI memory that never forgets.

### 02 Creativity & Innovation
Applying Cognee's hybrid graph-vector memory to legal contradiction tracking is novel. Most AI legal tools are stateless wrappers over LLMs. CourtMind's key insight: **contradiction detection across time requires persistent graph memory** — which is exactly what Cognee provides. The knowledge graph structure allows contradictions to be stored as relationships, not just text, enabling genuine cross-document reasoning.

### 03 Technical Excellence
- Clean module ownership: one file per concern (see `CONTEXT.md` file ownership table)
- All Cognee calls isolated in `memory_store.py` — zero Cognee imports elsewhere
- All Qwen calls isolated in `qwen_client.py` — zero direct API calls elsewhere
- All prompt text in `prompts.py` — no inline prompts anywhere
- Full async throughout (FastAPI + async Cognee operations)
- Typed with TypedDict and type hints
- LangGraph state machine for clean intent routing

### 04 Best Use of Cognee
- All four lifecycle stages used meaningfully: `remember`, `recall`, `improve`, `forget`
- Cognee is the **only** persistent storage layer — no SQL, no files, no Redis
- One dataset per case for proper isolation and scoped forgetting
- `recall()` used in two distinct modes: candidate lookup (contradiction detection) and answer synthesis (Q&A)
- `improve()` / `memify()` used for automated staleness handling — old assertions deprioritised when new information supersedes them
- `forget()` used for complete case archival — demonstrates Cognee's full lifecycle from creation to deletion

### 05 User Experience
- Four focused screens: Ingest → Query → Contradictions → Brief
- Case selector with inline case creation
- Real-time contradiction display on ingestion
- Confidence bars and severity indicators on contradictions
- Works immediately — no setup beyond API keys

### 06 Presentation Quality
This README covers the problem, solution, architecture, and judging criteria. See `docs/` for detailed HLD, LLD, API contract, test cases, and build log.

---

## Quickstart

### Backend

```bash
cd backend
pip install -r requirements.txt

# Copy and fill in your credentials:
cp ../.env.example .env
# Set COGNEE_API_KEY and COGNEE_TENANT_URL from platform.cognee.ai
# Set DASHSCOPE_API_KEY from dashscope-intl.aliyuncs.com

uvicorn main:app --reload --port 8000
```

**Getting Cognee Cloud credentials:**
1. Sign up at [platform.cognee.ai](https://platform.cognee.ai/sign-in)
2. Use promo code `COGNEE-35` for $35 free Developer credit
3. Navigate to API Keys in the sidebar → create a key
4. Copy your tenant URL from the dashboard

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
# Open http://localhost:3000
```

---

## Cognee Cloud SDK — Resolved API Changes

**Critical finding for anyone migrating from older docs:** The Cognee Cloud SDK has updated its API. The old `cogwit-sdk` package and `cogwit_instance.method()` pattern is no longer the recommended approach.

**Current (correct) pattern:**
```python
import cognee

# Connect to your Cognee Cloud tenant
await cognee.serve(url="https://your-tenant.aws.cognee.ai", api_key="your-key")

# Operations using new method names:
await cognee.remember(text, dataset_name=case_id)   # replaces add() + cognify()
results = await cognee.recall(query_text=query)      # replaces search()
await cognee.improve(dataset_name=case_id)           # replaces memify()
await cognee.forget(dataset_name=case_id)            # replaces dataset deletion
await cognee.disconnect()                            # cleanup
```

Lower-level ops (`add`, `cognify`, `search`, `memify`) remain available for fine-grained control.

Source: [docs.cognee.ai/cognee-cloud/connections/cloud-sdk](https://docs.cognee.ai/cognee-cloud/connections/cloud-sdk)

---

## Project Structure

```
courtmind/
├── backend/
│   ├── main.py                # FastAPI routes
│   ├── langgraph_agent.py     # LangGraph orchestrator
│   ├── cognee_config.py       # Cognee Cloud connection
│   ├── memory_store.py        # ALL Cognee operations (only file that imports cognee)
│   ├── qwen_client.py         # ALL Qwen API calls (only file that calls Qwen)
│   ├── extractor.py           # Assertion extraction
│   ├── contradiction_detector.py # Contradiction detection
│   ├── answer_builder.py      # Q&A synthesis
│   ├── brief_generator.py     # Trial brief generation
│   ├── prompts.py             # All prompt constants
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Landing page
│   │   ├── ingest/page.tsx    # Document ingestion
│   │   ├── query/page.tsx     # Q&A interface
│   │   ├── contradictions/page.tsx
│   │   └── brief/page.tsx     # Trial brief generator
│   ├── components/
│   │   └── CaseSelector.tsx
│   └── lib/api.ts             # All API calls
├── docs/
│   ├── HLD.md                 # High level design
│   ├── LLD.md                 # Low level design
│   ├── CONTEXT.md             # Project context + rules
│   ├── API_CONTRACT.md        # API shapes
│   ├── PROMPTS.md             # All prompts
│   ├── TEST_CASES.md          # Test fixtures + demo script
│   ├── BUILD_LOG.md           # Session-by-session build log
│   └── Roadmap.md             # Day-by-day plan
├── .env.example
├── LICENSE
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangGraph |
| Memory layer | **Cognee Cloud** via `cognee` package + `cognee.serve()` |
| AI Reasoning | Qwen 2.5-72B via Qwen Cloud (DashScope international endpoint) |
| Frontend Deploy | Vercel |
| Backend Deploy | Alibaba Cloud ECS |

---

## License

MIT — open source, public repository.

---

*Submitted to: Cognee Hackathon "The Hangover Part AI" — WeMakeDevs (Jul 5, 2026 deadline)*  
*Also submitted to: Qwen Cloud Global AI Hackathon Track 1 — MemoryAgent (Jul 9, 2026 deadline)*
