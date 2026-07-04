# CourtMind — Project Context (CONTEXT.md)

**Paste this at the top of EVERY new AI coding session, regardless of which model you're using (Claude, GPT, Gemini, etc).**  
**This file is the single source of truth for how this codebase works. If anything here conflicts with what a model assumes, this file wins.**

---

## What This Project Is

CourtMind is a legal litigation memory assistant. It ingests legal documents (witness statements, depositions, contracts, emails), extracts factual assertions, detects contradictions between them, tracks staleness when new information arrives, supports natural-language Q&A over case memory, and generates trial-prep briefs.

One codebase. Submitted to two hackathons:
- **Cognee Hackathon — "The Hangover Part AI"** (WeMakeDevs) — targeting the **Best Use of Cognee Cloud** prize specifically (Apple iPhone 17)
- **Qwen Cloud Global AI Hackathon** Track 1: MemoryAgent — judged on persistent agent memory using Qwen models

There is no separate "Cognee version" and "Qwen version." It is one architecture, one repo, one build.

---

## Core Architecture in One Paragraph

**Cognee** is the memory layer. **Qwen2.5-72B** is the reasoning layer. **LangGraph** is the orchestrator that routes requests between them. **Next.js** is the frontend. Cognee has no language understanding of its own — it only stores and retrieves. Qwen has no memory of its own — every call is stateless and only knows what's put directly in front of it. Together: Cognee remembers, Qwen thinks, LangGraph decides what to do next.

**Build strategy — open source now, Cognee Cloud later, if at all:** Cognee Cloud (`platform.cognee.ai`) is currently at signup capacity — this team and many others cannot create an account. The build therefore uses the **open-source `cognee` pip package** (self-hosted, no signup required) as the primary and current target. Every Cognee call lives inside exactly one file, `memory_store.py`, so that IF Cognee Cloud signup opens before the submission deadline, migrating to `cogwit-sdk` is a contained, single-file change (see `LLD.md` Sections 0, 3.3A, and 10 for the full migration path). **Do not install or import `cogwit_sdk` unless this migration has actually been triggered** — until then, this codebase uses `cognee` only.

---

## Tech Stack — Exact Versions (verify and update Day 1 of build)

| Layer | Technology | Version (to confirm) |
|---|---|---|
| Language (backend) | Python | 3.11 |
| Web framework | FastAPI | 0.111.x |
| Agent orchestration | LangGraph | latest 0.2.x at build time |
| AI client | `openai` SDK (Qwen-compatible) | 1.35.x |
| AI model (inference) | qwen2.5-72b-instruct | via Qwen Cloud DashScope, base URL `dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| Memory layer (current) | `cognee` (open-source pip package) | latest at build time — confirm exact method signatures Day 1 |
| Memory layer (migration target, conditional) | `cogwit-sdk` | only install/use if Cognee Cloud signup access is actually obtained |
| Frontend framework | Next.js | 14 (App Router) |
| Frontend styling | Tailwind CSS | 3.x |
| Node version | Node.js | 20 LTS |

**Action for Day 1:** Confirm `cognee`'s exact `cognify()` parameter name (`datasets` vs `dataset_ids`), `search()`'s exact signature and return shape, `memify()`'s exact invocation and effect, and the correct dataset deletion/pruning call. Log all findings in `BUILD_LOG.md` before writing code that depends on them.

---

## File Ownership — Never Cross These Boundaries

| File | Owns | Never put elsewhere |
|---|---|---|
| `qwen_client.py` | ALL Qwen API calls for reasoning (chat completions) | No other file calls Qwen's chat API directly |
| `cognee_config.py` | Cognee LLM + embedding provider configuration (open-source build) — becomes `cogwit_instance` client setup if migrated to Cognee Cloud | No business logic here |
| `memory_store.py` | ALL Cognee operations — add, cognify, search, memify, archive. This is the ONLY file that imports `cognee` (or `cogwit_sdk` after migration). | No other file calls Cognee/cogwit directly. No Qwen reasoning calls here. |
| `extractor.py` | Assertion extraction logic only | No memory calls here |
| `contradiction_detector.py` | Contradiction comparison logic only | Calls `memory_store.recall_chunks()` for candidates, but contradiction judgment itself is Qwen-only |
| `answer_builder.py` | Answer synthesis from recalled memory | No memory writes here |
| `brief_generator.py` | Trial brief generation only | No memory writes here |
| `prompts.py` | Loads prompt strings from PROMPTS.md content as constants | No prompt text written inline anywhere else |
| `langgraph_agent.py` | Agent graph definition, state, and routing only | No direct Qwen or Cognee Cloud calls — it calls the modules above |
| `main.py` | FastAPI route definitions only | No business logic here — routes call `langgraph_agent.py` |

**Rule:** if you (the AI model) are about to write a Qwen API call or a Cognee call (`cognee.xxx()` or `cogwit_instance.xxx()`) inside a file other than `qwen_client.py` or `memory_store.py`, stop — that logic belongs in one of those two files, called from wherever you are.

**Rule:** do not `import cognee` or `import cogwit_sdk` in `requirements.txt`/code unless that is the currently active memory backend. The current backend is **open-source `cognee`**. Only switch to `cogwit_sdk` if Cognee Cloud signup access has actually been obtained and the migration checklist in `LLD.md` Section 10 has been followed — check `BUILD_LOG.md` for the current status before assuming either way.

---

## Prompts — Critical Rule

ALL prompt text lives in `PROMPTS.md`. Every prompt used anywhere in the code must match what's documented there exactly.

**Never write a new prompt inline in code.** If a prompt needs to change, update `PROMPTS.md` first, log the change and reason in `BUILD_LOG.md`, then update the code to match.

---

## Environment Variables

```python
from dotenv import load_dotenv
load_dotenv()
import os

DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]   # Qwen Cloud — used by qwen_client.py AND cognee_config.py (LLM/embedding provider for open-source cognee)

# Only required if migrated to Cognee Cloud — check BUILD_LOG.md for current status:
# COGWIT_API_KEY = os.environ["COGWIT_API_KEY"]
```

Never hardcode keys. Never commit `.env`. Always check `.env.example` for the current full list of required vars.

---

## Error Handling Rules

1. **Never swallow errors silently.** No bare `except: pass`.
2. **Always log errors** with `print(f"[ERROR] {module_name}: {e}")` — sufficient for hackathon scope.
3. **Qwen API errors** — wrap in try/except, return `{"error": str(e)}` to the calling route, let FastAPI return HTTP 500.
4. **Cognee errors** — wrap every `memory_store.py` call in try/except. Cognee operations are async and can fail on network or provider config issues; log clearly which operation failed (`add`, `cognify`, `search`, `memify`, archive/delete).
5. **JSON parsing** — every `json.loads()` call on a Qwen response must be wrapped in try/except. If parsing fails, log the raw response text before raising.

```python
# Standard error pattern — use this everywhere
try:
    result = some_operation()
except Exception as e:
    print(f"[ERROR] {__name__}: {e}")
    raise
```

---

## Coding Conventions

- **Async:** Use `async def` for all FastAPI routes and all `memory_store.py` functions (`cognee`'s functions are async). Qwen calls via `qwen_client.py` stay synchronous — the `openai` SDK handles this fine.
- **Type hints:** Always add type hints to function signatures.
- **No classes:** Keep everything as functions for hackathon simplicity, except the one `cogwit_instance` client object which is inherently a class instance per the SDK's own design.
- **Imports:** Group as stdlib → third-party → local, one blank line between groups.
- **Return types:** All API routes return dicts that FastAPI serialises to JSON.
- **Case IDs:** Always pass `case_id` as a string. This doubles as the Cognee Cloud `dataset_name` — keep that mapping consistent everywhere (one dataset per legal case). Note that `add()` also returns a separate `dataset_id` (a Cognee-generated identifier) that's needed for `cognify()` and deletion calls — track both `case_id` (ours) and `dataset_id` (Cognee's) together, do not conflate them.

---

## Memory Model — What "Remembering" Actually Means Here

- One **Cognee Cloud dataset per case** (`dataset_name = case_id`, with Cognee's own `dataset_id` tracked alongside it).
- Ingesting a document → extract assertions (Qwen) → `add()` each into Cognee Cloud → `cognify()` to build/update the graph → `search()` with `CHUNKS` to find contradiction candidates → Qwen judges contradictions → store any found contradictions back via `add()` + `cognify()` → `memify()` to enrich and flag staleness.
- Querying → `search()` with `GRAPH_COMPLETION` against the case's dataset → hand results to Qwen → synthesise an answer with citations.
- Archiving a case → delete the case's Cognee Cloud dataset (exact method TBC, see `BUILD_LOG.md`), not a full wipe of all memory.

**Do not build a parallel memory system.** If a model is tempted to add a SQL table, a JSON file, or any other persistent store "just to keep track of X," that's a sign the task should go through Cognee Cloud instead. The only exception is ephemeral request-scoped state inside `langgraph_agent.py`'s `AgentState`, which does not persist between requests.

---

## LangGraph Agent State Shape

```python
from typing import TypedDict, Literal

class AgentState(TypedDict):
    input: str          # raw user input text
    case_id: str         # active case identifier, doubles as Cognee Cloud dataset_name
    intent: str          # "ingest" | "query" | "brief"
    result: dict          # output from whichever node ran
    error: str | None     # error message if any step failed
```

Do not add new fields without updating this file and `BUILD_LOG.md`.

---

## API Base URL

- **Local dev:** `http://localhost:8000`
- **Deployed (Alibaba Cloud ECS):** set in frontend `.env.local` as `NEXT_PUBLIC_API_URL`
- **All backend routes prefixed:** `/api/`

---

## What an AI Model Should NOT Do on This Project

- Do not install or reference the open-source `cognee` package — always `cogwit-sdk`
- Do not install new pip/npm packages without first checking `requirements.txt` / `package.json` for an existing equivalent
- Do not invent a database schema — there is none; Cognee Cloud owns all persistent storage
- Do not rewrite prompts inline — use `PROMPTS.md` via `prompts.py`
- Do not add authentication/authorization logic — explicitly out of scope for the hackathon build
- Do not guess at `cogwit-sdk` return shapes without checking the installed SDK / official docs first — verify, then log the finding in `BUILD_LOG.md`
- Do not create new files without first checking the file ownership table above for whether the logic already has a home

---

## Where to Look Before Asking Questions

| Question | Look here first |
|---|---|
| "What does this feature do?" | `HLD.md` |
| "How exactly is X implemented / what's the function signature?" | `LLD.md` |
| "What prompt should I use for X?" | `PROMPTS.md` |
| "What did the last session decide or change?" | `BUILD_LOG.md` |
| "What's been built so far, what's left?" | `BUILD_LOG.md` + `PROGRESS.md` |
| "What test input should I use to verify this works?" | `TEST_CASES.md` |
| "What does the API expect/return for this endpoint?" | `API_CONTRACT.md` |
| "What's the day-by-day plan?" | `Roadmap.md` |

---

*Update this file only when a fundamental architectural decision changes — not for routine implementation details (those go in BUILD_LOG.md).*
