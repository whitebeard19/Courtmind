# CourtMind

**A litigation memory agent that never forgets — and never lets a witness get away with a contradiction.**

CourtMind ingests legal documents (depositions, witness statements, incident reports, contracts) into a **persistent knowledge graph**, then automatically detects **factual contradictions** between statements — even when the conflicting accounts arrive weeks apart, in different documents, from different people. It answers natural-language questions over the entire case memory with sourced, contradiction-aware answers, and generates trial-prep briefs.

Built for the Cognee "The Hangover Part AI" hackathon (persistent AI memory) and the Qwen Cloud Global AI Hackathon (Track 1 — MemoryAgent).

---

## The problem

A single litigation case can involve thousands of pages of testimony from dozens of witnesses. The most valuable fact in the whole case is often a **contradiction** — Witness A says the meeting was Tuesday, Witness B says Thursday; the inspector says she never checked the equipment, the supervisor says she cleared it. These conflicts win or lose cases.

But no human — and no stateless chatbot — reliably catches them. A contradiction only surfaces if you happen to remember, months later, that someone said the opposite in a document you read in week one. Human working memory doesn't scale to that. Neither does an LLM with a context window.

**CourtMind is the memory that does.** Every fact a witness states is permanently structured into a knowledge graph. The moment a new statement conflicts with anything ever said in the case, it's flagged — with the two statements, a plain-English reason, and a confidence score.

---

## What it does

- **Ingest** any legal document as free text → CourtMind extracts the discrete factual assertions (who said what, when, about which event).
- **Detect contradictions** automatically on every ingest — comparing each new assertion against the entire case memory, not just the current document. False positives are actively guarded against (sequential events like "arrived 2:00 PM" / "left 3:15 PM" are *not* flagged).
- **Ask questions** in natural language ("When was the safety inspection completed?") and get a **sourced, contradiction-aware answer** drawn from the persistent graph — across sessions, even after a full restart.
- **Generate a trial brief** — an executive summary, ranked top contradictions with recommended actions, unresolved questions, and key assertions.
- **Manage case lifecycle** — archive a case and its memory is surgically deleted.

---

## Why this is a real use of persistent memory

The headline feature is impossible without persistent, cross-session memory:

- The contradiction between Document 1 (week one) and Document 12 (week six) is only catchable if Document 1's facts are still queryable when Document 12 arrives.
- The Q&A works from a **cold start** — restart the entire backend, ask a question about a case ingested days earlier, and you get a sourced answer. Nothing lives in the request; everything lives in Cognee.

This is a MemoryAgent in the truest sense: the agent's value grows monotonically with everything it has ever ingested.

---

## Best use of Cognee — the memory lifecycle

CourtMind is built directly on **Cognee Cloud's** hybrid graph + vector memory. All Cognee operations live in a single module (`backend/memory_store.py`) — no other file touches the memory layer. We use Cognee's flagship lifecycle API:

| Cognee op | Where CourtMind uses it | What it does for us |
|---|---|---|
| **`remember()`** | Every ingested assertion and every detected contradiction | Ingests the text and permanently **structures it into the knowledge graph** in one call — the system of record for the entire case |
| **`recall()`** | The Q&A screen and brief generation | **Auto-routes between semantic similarity and graph traversal** and returns a graph-grounded answer that is already contradiction-aware — it surfaces conflicting facts on its own |
| **`forget()`** | Archiving a case | **Surgically deletes** a case's entire dataset from memory when it's retired |

Each legal case maps 1:1 to a Cognee **dataset** (`dataset_name = case_id`), giving clean per-case isolation over the shared graph-vector store.

**On enrichment (`improve()` / `memify()`):** these lifecycle operations are not enabled on our Cognee Cloud tenant (the tenant's API does not expose the `/improve` endpoint, and the central enrichment host is not reachable from our build network). We wired the call and disclose this honestly rather than fake it. CourtMind's core value — persistent structured memory and cross-session contradiction detection — is fully delivered by `remember` / `recall` / `forget`.

---

## Architecture

```
        ┌──────────────────────────┐
        │       Next.js UI          │   /ingest  /query  /contradictions  /brief
        │  (React + Tailwind, TS)   │   + CaseSelector
        └─────────────┬────────────┘
                      │  REST (JSON)
                      ▼
        ┌──────────────────────────────────────────────┐
        │        FastAPI  +  LangGraph agent             │
        │  classify_intent → ingest / query / brief      │
        │                                                │
        │  extractor.py   contradiction_detector.py      │
        │  answer_builder.py   brief_generator.py        │
        └───────┬───────────────────────────┬───────────┘
                │                            │
   reasoning    │                            │  memory (only client)
                ▼                            ▼
   ┌─────────────────────────┐   ┌──────────────────────────────┐
   │  Qwen (qwen-plus) via    │   │        memory_store.py         │
   │  Alibaba Cloud DashScope │   │  remember() · recall() ·        │
   │  extraction, contradiction│  │  forget()  → Cognee Cloud       │
   │  judgment, answers, brief │  │  (hybrid graph + vector memory) │
   └─────────────────────────┘   └──────────────────────────────┘
                                              │
                          per-case dataset ( dataset_name = case_id )
```

**Two brains, cleanly separated:**
- **Cognee Cloud** is the *memory* — the persistent hybrid graph-vector store of every fact and contradiction, per case.
- **Qwen** (Alibaba Cloud DashScope) is the *reasoning* — it extracts assertions, judges contradictions, and synthesizes answers and briefs.
- **LangGraph** orchestrates the agent: it classifies each request and routes to the ingest, query, or brief path.

### How an ingest flows

1. **Extract** — Qwen turns the raw document into discrete assertions (`text`, `speaker`, `event_date`, `entities`).
2. **Remember** — each assertion is `remember()`-ed into the case's Cognee dataset (fire-and-forget, so a slow cloud call never blocks the response), and mirrored into a fast in-memory **write-through cache**.
3. **Detect** — each new assertion is compared (via Qwen) against the case's full assertion set from the cache. Confirmed contradictions (≥ 0.7 confidence, with a reason-consistency guard) are `remember()`-ed back into the graph as contradiction relationships.
4. **Return** — the API returns extracted assertions + detected contradictions immediately.

### An engineering decision worth calling out

Cognee Cloud's `recall`/`search` has an eventual-consistency window right after ingestion, which made real-time contradiction detection intermittently miss just-stored facts. Rather than let the centerpiece feature depend on that timing, we keep a **write-through cache** of every stored assertion and drive contradiction detection from it — so detection is **instant and deterministic**, while Cognee remains the persistent system of record for Q&A, cross-session recall, and archival. It's a standard cache-in-front-of-a-store pattern, applied where reliability matters most.

---

## Tech stack

- **Memory:** Cognee Cloud (hybrid graph + vector), `cognee` SDK 1.2.2
- **Reasoning:** Qwen `qwen-plus` (Qwen2.5-based) via Alibaba Cloud DashScope (OpenAI-compatible endpoint)
- **Agent / API:** Python, FastAPI, LangGraph
- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS, react-markdown
- **License:** MIT

---

## Getting started

### Prerequisites
- **Python 3.11 or 3.12** (Cognee does not support 3.13+)
- **Node.js 18+**
- A **Cognee Cloud** account (API key + tenant URL)
- An **Alibaba Cloud DashScope** API key (international endpoint)

### 1. Backend

```bash
cd backend
python -m venv venv                      # use a 3.11/3.12 interpreter
# Windows:
./venv/Scripts/python.exe -m pip install -r requirements.txt
# macOS/Linux:
# ./venv/bin/python -m pip install -r requirements.txt
```

Create `.env` in the project root:

```bash
# Qwen Cloud (DashScope)
DASHSCOPE_API_KEY=sk-...
QWEN_MODEL=qwen-plus                      # or qwen-max / qwen-turbo

# Cognee Cloud
COGNEE_API_KEY=...
COGNEE_TENANT_URL=https://<your-tenant>.aws.cognee.ai

# Disable Cognee's conversational session memory so retrieval returns stored
# facts rather than chat-style replies (required)
CACHING=false
```

Run the API (do **not** use `--reload` during a demo — it resets in-memory state):

```bash
./venv/Scripts/python.exe -m uvicorn main:app --port 8000
```

Health check: `http://localhost:8000/` — interactive API docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                               # http://localhost:3000
```

---

## Using it — a worked example

Create a case, then ingest these two statements (as separate ingests, same case):

> **Kline Deposition** (speaker: Sarah Kline): *"Nordic was required to deliver the platform by March 1, 2025. The total contract value was $50,000."*

> **Torenn Statement** (speaker: David Torenn): *"The contract required delivery by March 15, 2025. The total contract value was $65,000."*

On the second ingest, CourtMind flags **two contradictions** — the delivery date (March 1 vs March 15) and the contract value ($50,000 vs $65,000) — each with a reason and confidence. Then ask on the **Query** screen: *"What was the delivery deadline?"* — and you get a sourced answer that names both parties and states the conflict, straight from Cognee's `recall()`.

---

## API reference

Base URL: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). All bodies are JSON; `case_id` is also the Cognee dataset name.

| Method & path | Purpose |
|---|---|
| `POST /api/cases` | Create a case → `{ case_id, name, status, created_at }` |
| `GET /api/cases` | List cases for the selector |
| `POST /api/ingest` | Ingest a document → `{ assertions_extracted, contradictions_found, assertions[], contradictions[] }` |
| `POST /api/query` | Ask a question → `{ answer, sources[] }` |
| `POST /api/brief` | Generate a trial brief → `{ top_contradictions[], unresolved_questions[], key_assertions[], brief_summary }` |
| `GET /api/contradictions?case_id=&min_confidence=` | List a case's contradictions |
| `PATCH /api/cases/{case_id}/archive` | Archive a case (Cognee `forget`) |

A contradiction is: `{ assertion_a, assertion_b, reason, confidence }`.

---

## Design highlights (technical)

- **Single memory boundary** — only `memory_store.py` imports `cognee`; every other module is memory-agnostic.
- **Resilient by construction** — Cognee persistence is fire-and-forget and never blocks or aborts the request; contradiction detection runs off the write-through cache, so the centerpiece works even if the cloud is slow or degraded.
- **False-positive guards** — the contradiction prompt distinguishes *sequential events* (arrival before departure) from genuine conflicts, and a code-level guard rejects any verdict whose own reasoning text says the statements are compatible.
- **Clean output** — ingestion metadata is stripped from user-facing statements; near-duplicate contradictions are de-duplicated.
- **Survives restarts** — case metadata, contradictions, and the assertion cache persist to disk, so a backend restart never loses the case list (the graph itself lives in Cognee).

---

## Known limitations (honest)

- **Ingest latency:** each document takes several seconds to tens of seconds, dominated by LLM extraction/judgment and cloud persistence. For live demos, pre-ingest documents. Contradiction results return as soon as detection completes.
- **Enrichment / staleness (`improve`/`memify`):** not enabled on our Cognee tenant (endpoint not exposed; central enrichment host unreachable from our network). Wired but inactive — disclosed rather than faked.
- **Ingestion is text-paste only** in this version (no PDF/OCR).
- **Auth / multi-user** is out of scope for this prototype.

---

## AI-assistant disclosure

Per the Cognee Hackathon rules, we disclose that this project was built with the assistance of AI coding tools (Anthropic Claude). All architectural decisions, Cognee/Qwen integration, debugging, and testing were directed and verified by the team; AI was used as a pair-programming and drafting aid.

---

## License

MIT — see [LICENSE](LICENSE).
