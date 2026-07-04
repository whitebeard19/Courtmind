# CourtMind — Frontend Build Prompt (Day 4)

> Paste this whole file to the AI/session building the frontend. It is self-contained:
> it embeds the exact, **already-verified** backend API contract and all the backend
> quirks discovered during testing. The backend (Days 1–3) is complete and confirmed
> working live against Cognee Cloud + Qwen. Your job is ONLY the frontend.
>
> Source-of-truth docs if you need more depth: `docs/API_CONTRACT.md`,
> `docs/LLD.md` (§5 component map, §6 env), `docs/TEST_CASES.md` (demo script),
> `docs/CONTEXT.md`, `docs/HLD.md`. **Where this prompt and older docs disagree, THIS
> prompt wins** — it reflects the backend as actually built and tested.

---

## 1. What CourtMind is

A litigation memory assistant for lawyers. You paste documents (depositions, statements)
into a **case**; the backend extracts factual assertions, stores them in a persistent
knowledge graph (Cognee Cloud), and **detects contradictions** between statements
(e.g. one witness says a meeting was Tuesday March 12, another says Thursday March 14).
You can then ask natural-language questions over the case memory and generate a trial-prep
brief. The headline feature is **contradiction detection**; the second theme is **memory
that persists across sessions**.

## 2. Tech stack & setup

- **Next.js 14 (App Router) + TypeScript + Tailwind CSS.** Client components for the
  interactive pages (`"use client"`).
- A scaffold may already exist under `frontend/` from an earlier pass. It was written
  **before** the backend was verified, so treat it as a starting point only and reconcile
  every API call against the contract in §4 below (the contract is authoritative).
- Config — create `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
  (For deployment this becomes the Alibaba Cloud ECS IP, e.g. `http://<ecs-ip>:8000`.)
- Run: `cd frontend && npm install && npm run dev` → http://localhost:3000
- The backend has permissive CORS (`allow_origins=["*"]`), so no CORS setup is needed.

## 3. App structure (target)

```
/app
  layout.tsx                 → global navbar containing the CaseSelector; wraps all pages
  page.tsx                   → redirect or landing → /ingest
  /ingest/page.tsx           → DocumentIngestForm + extracted assertions + contradictions found
  /query/page.tsx            → question box + sourced answer
  /contradictions/page.tsx   → contradiction list with confidence bars
  /brief/page.tsx            → generate-brief button + structured brief display
/components
  CaseSelector.tsx           → dropdown of cases + inline "create case"
  AssertionCard.tsx
  ContradictionCard.tsx      → shows A vs B, reason, confidence bar
/lib
  api.ts                     → all fetch calls, typed
```

The **active case** is global state (the selected `case_id`). Persist it in `localStorage`
so it survives navigation/reload. Every page except case creation requires an active case —
if none is selected, show a prompt to pick/create one and disable actions.

---

## 4. API CONTRACT (verified — match exactly)

Base URL = `process.env.NEXT_PUBLIC_API_URL`. All bodies are JSON. `case_id` is a short
string (8 chars). Confidence/score values are floats 0.0–1.0.

### `POST /api/cases` — create case
Request: `{ "name": string, "description"?: string }`
Response 200: `{ "case_id": string, "name": string, "status": "active", "created_at": ISO8601 }`

### `GET /api/cases` — list cases (for the selector)
Response 200: `{ "cases": [ { "case_id": string, "name": string, "status": "active"|"archived", "created_at": ISO8601 } ] }`

### `POST /api/ingest` — ingest a document  ⏱️ SLOW (see §5)
Request:
```json
{ "case_id": string, "document_text": string, "source_label": string, "speaker"?: string }
```
Response 200:
```json
{
  "assertions_extracted": 4,
  "contradictions_found": 2,
  "assertions": [ { "text": string, "speaker": string|null, "event_date": string|null } ],
  "contradictions": [ { "assertion_a": string, "assertion_b": string, "reason": string, "confidence": 0.91 } ]
}
```

### `POST /api/query` — ask a question  ⏱️ ~10s
Request: `{ "case_id": string, "question": string }`
Response 200: `{ "answer": string, "sources": string[] }`
- `answer` is full prose and **may contain markdown** (e.g. `**bold**`, `[1]` citations).
  Render markdown or at least preserve line breaks; don't assume plain text.
- `sources` is an **array of strings**, each a numbered context chunk like
  `"[1] The quarterly review meeting took place on Tuesday... [Speaker: John Martinez] ..."`.
  Render each as a list item / collapsible. Do **not** assume nested objects/fields.

### `POST /api/brief` — generate trial brief  ⏱️ SLOW (~60s)
Request: `{ "case_id": string, "case_name": string, "max_words": 500 }`
Response 200:
```json
{
  "top_contradictions": [ { "summary": string, "assertion_a": string, "assertion_b": string,
                            "severity": "high"|"medium"|"low", "recommended_action": string } ],
  "unresolved_questions": string[],
  "key_assertions": [ { "text": string, "source": string, "importance": string } ],
  "brief_summary": string
}
```

### `GET /api/contradictions` — list contradictions (query params, not body)
`GET /api/contradictions?case_id=<id>&min_confidence=0.5`
Response 200: `{ "contradictions": [ { "assertion_a": string, "assertion_b": string, "reason": string, "confidence": 0.91 } ] }`

### `PATCH /api/cases/{case_id}/archive` — archive a case
Response 200: `{ "case_id": string, "status": "archived" }`

---

## 5. CRITICAL backend behaviors — design around these

1. **Ingest and brief are SLOW.** Measured live: ingest **~40–70s** per document, brief
   **~60s**, query **~10s**. This is inherent (cloud graph build + many LLM calls). You MUST:
   - Set a generous client timeout — **180s** (3 min) — on ingest/brief fetches, or they'll
     abort. (Default `fetch`/axios timeouts are far too short.)
   - Show a clear **loading state** with a spinner and a "this can take up to a minute"
     message. Never block silently. Disable the submit button while in flight.
   - Consider an elapsed-time counter so the user knows it's working.

2. **Error response shape is inconsistent.** Success is as documented. Errors may arrive as
   either `{ "error": "..." }` (documented) **or** `{ "detail": "..." }` (FastAPI
   `HTTPException`, what the backend actually emits on 4xx/5xx). Your API layer must check
   **both** keys and surface a readable message. Always check `response.ok` first.

3. **Contradictions may contain near-duplicates.** One real conflict (e.g. the Mar-12 vs
   Mar-14 date) can show up as several entries (the new statement vs each prior matching
   chunk), all `confidence: 1.0`. That's expected. The UI should render a clean list;
   optionally group/dedupe by the `(assertion_a, assertion_b)` pair, but listing them is fine.

4. **`confidence` is 0.0–1.0** → render as a percentage and a colored confidence bar.
   ≥0.85 = strong (red/high), 0.7–0.85 = medium (amber), below = low. Backend only stores
   contradictions ≥0.7.

5. **No staleness data on the wire.** The memify/`improve()` staleness feature is currently
   non-functional (returns 404 on the backend, caught and ignored). So **do NOT build a
   StalenessBadge or any staleness UI** — there's no field for it. Skip it entirely for now.

6. **Assertions** have nullable `speaker` and `event_date` — render "Unknown" / hide when null.

7. **Persistence is real and cross-session.** Memory lives in Cognee Cloud keyed by
   `case_id`, not in the browser or server RAM. A case ingested earlier is fully queryable
   later. (Caveat: the cases *list* and the contradictions feed are partly held in backend
   process memory, so a backend restart can empty the case dropdown even though the
   underlying memory persists — not your concern for the frontend, just don't be surprised.)

---

## 6. Screen specs

**Global navbar (layout.tsx):** product name "CourtMind", nav links (Ingest / Query /
Contradictions / Brief), and the **CaseSelector** on the right. Selected case shown
prominently. Professional, legal-tech look (clean, serious, lots of whitespace; a deep
navy/slate accent works well). Tailwind.

**CaseSelector.tsx:** on mount `GET /api/cases` to populate a dropdown. Selecting sets the
active case (localStorage). An inline "+ New case" reveals a name field → `POST /api/cases`
→ refresh list → auto-select the new case. If no cases exist, prompt to create one.

**/ingest:** form fields — `document_text` (large textarea), `source_label` (text, e.g.
"Martinez Deposition p.1"), `speaker` (optional text). Submit → `POST /api/ingest` (long
loading state). On success show: count of assertions extracted, list of **AssertionCards**
(text, speaker, date), and — if any — a highlighted **"⚠️ N contradictions found"** section
rendering **ContradictionCards** (A vs B, reason, confidence bar). All inputs are typed
freely by the user — do NOT add canned/"load demo" buttons; the demo showcases real typing
into the live UI and uses different documents/questions each time.

**/query:** question textbox + ask button → `POST /api/query`. Render the `answer`
(markdown-aware) prominently, and the `sources` list below as collapsible/numbered context
items. Loading + empty states.

**/contradictions:** on load (and on a refresh button) call
`GET /api/contradictions?case_id=...&min_confidence=0.5`. Render ContradictionCards sorted
by confidence desc, each with the confidence bar and severity color. Empty state: "No
contradictions detected in this case yet."

**/brief:** a "Generate brief" button → `POST /api/brief` with `{ case_id, case_name,
max_words: 500 }` (long loading state ~60s). Render: `brief_summary` at top; a
**top_contradictions** section (each: summary, A vs B, severity badge, recommended action);
**unresolved_questions** as a bulleted list; **key_assertions** as a list (text + source +
importance).

States for every page: **empty** (no case / no data), **loading** (spinner + message),
**error** (readable message from `error`/`detail`), **success**.

---

## 7. Reference test data (for YOUR testing only — NOT baked into the UI)

Use this only to manually test your build. The real demo will use **different documents and
questions typed live each time**, so do not hardcode any of this into buttons, placeholders,
or defaults. Inputs are always free-form.

- Doc (source `"Martinez Deposition p.1"`, speaker `"John Martinez"`):
  > I attended the quarterly review meeting on Tuesday, March 12, 2024. The meeting took place at the downtown office on Fifth Street. I signed the updated vendor contract at the end of the meeting. Sarah Chen was also present.
- Conflicting doc (source `"Chen Statement"`, speaker `"Sarah Chen"`):
  > The quarterly review meeting was held on Thursday, March 14, 2024.
- Example question: `"What did Martinez say about the meeting date?"`

**Flow the UI must support (with arbitrary content):** create case → ingest one or more
documents → contradictions appear when statements conflict → /contradictions lists them with
confidence → /query returns a sourced, contradiction-aware answer → /brief summarizes the
case. Every screen is exercised live in the demo, so each must stand on its own with
free-form input.

---

## 8. Acceptance criteria

- All 4 pages + CaseSelector work against the live backend at `NEXT_PUBLIC_API_URL`.
- Long requests (ingest/brief) don't time out and show proper loading UI.
- The full demo narrative in §7 runs end-to-end through the UI.
- Errors (both `error` and `detail` shapes) render readable messages, never a blank screen.
- No staleness UI is built (no field exists yet).
- Matches the component map in `docs/LLD.md` §5 and the contract in `docs/API_CONTRACT.md`
  (as amended by §4–§5 here).
```
