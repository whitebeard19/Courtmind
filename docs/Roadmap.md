# CourtMind — Full Build Roadmap

**Version:** 5.0 — Compressed 6-Day Plan, Open Source `cognee` First  
**Build window:** 4 days build + 2 days test/polish/submit (6 days total, evenings, 2–3 hrs/day, 2-person team)  
**Hard rule:** No code before June 29 (Cognee Hackathon Rule 9). Today through June 28 is planning-only.  
**Memory strategy:** Build on open-source `cognee` now (Cognee Cloud signup is at capacity). Migrate to `cogwit-sdk`/Cognee Cloud only if signup access opens before submission — see `HLD.md` Section 3 and `LLD.md` Section 0.  
**Submission 1:** Cognee Hackathon "The Hangover Part AI" — July 5, 2026  
**Submission 2:** Qwen Cloud Global AI Hackathon Track 1 (MemoryAgent) — July 9, 2026

---

## How to Use This Document

Every day has a **goal**, a **build block** split between Person 1 (P1) and Person 2 (P2), and a **deliverable** — something committed to GitHub before you stop. At the end of every session, update `BUILD_LOG.md` and `PROGRESS.md`. This plan is tight — there is very little slack, so do not skip the deliverable check at the end of each day.

---

## Phase 0 — Planning Window (Now → June 28)

**No code. Only documents, sketches, and account setup that doesn't involve writing project code.**

- Read `HLD.md`, `LLD.md`, `CONTEXT.md`, and this roadmap together, end to end
- Both of you understand: we build on open-source `cognee` now, not `cogwit-sdk`, because Cognee Cloud signup is at capacity — and why that doesn't block either hackathon submission
- Try Cognee Cloud signup once more at `platform.cognee.ai/sign-in` — if it works, great, skip straight to the Cognee Cloud path in `LLD.md` Section 2A. If not, proceed with open-source as planned.
- Sign up for Qwen Cloud, request hackathon credits. If India isn't listed in a region dropdown, raise it in the Qwen Cloud Discord immediately — confirmed via official rules that India is not excluded, this is a signup form gap.
- Join the WeMakeDevs Discord and the Qwen Cloud Discord — also worth asking in the Cognee/WeMakeDevs Discord whether Cloud capacity is expected to clear during the hackathon window
- Create the GitHub repo skeleton: README stub and LICENSE file (MIT) only — no project logic yet
- Confirm P1/P2 roles for the schedule below

### Deliverable by June 28:
- Qwen Cloud account active, `DASHSCOPE_API_KEY` claimed
- Repo exists with LICENSE only
- Both people have read all docs fully

---

## Phase 1 — Build (Days 1–4 · Jun 29 – Jul 2)

### Day 1 — Jun 29 — Foundation: confirm cognee's real API, full project skeleton

**Goal:** Resolve the open-source `cognee` open items from `LLD.md` Section 9. Repo structure complete. First real Qwen call working.

**Build:**
- P1: `pip install cognee`, `pip install openai`, set up `.env` with `DASHSCOPE_API_KEY`. Write `cognee_config.py` per `LLD.md` Section 2.2. Write `qwen_client.py`, test with one call.
- P2: Write a throwaway test script — `cognee.add()` one sentence, `cognify()`, `search()` it back. Print the raw return objects to see their real shape. Confirm `cognify()`'s exact parameter name and whether it blocks or needs polling.
- Together: Resolve `LLD.md` Section 9 open items 1–5 (cognify/search signatures, memify invocation, deletion call, blocking behaviour). Update `BUILD_LOG.md` with confirmed answers. Create full folder structure per `LLD.md` Section 7. Write `prompts.py` loading all 6 prompts from `PROMPTS.md`.

**Deliverable:** One sentence stored, cognified, and retrieved via `cognee`. `qwen_client.py` working. Folder structure committed. `BUILD_LOG.md` updated with confirmed facts.

---

### Day 2 — Jun 30 — Memory pipeline + extraction

**Goal:** `extractor.py` and `memory_store.py` fully working per `LLD.md` Sections 3.2–3.3.

**Build:**
- P1: Write `extractor.py` using `qwen_client.infer()` + `EXTRACTION_PROMPT`. Run Test Case 1 from `TEST_CASES.md` — confirm JSON output parses correctly.
- P2: Write `memory_store.py`'s `store_assertion()`, `build_graph()`, `recall_chunks()`, `recall_answer()` per `LLD.md` Section 3.3. Test storing and retrieving Test Case 1 and Test Case 2's documents.
- Together: Confirm recall quality. If results are poor, adjust the text payload format in `store_assertion()`.

**Deliverable:** Full extract → store → recall loop working. `PROGRESS.md` Phases 1–2 (partial) checked.

---

### Day 3 — Jul 1 — Contradiction detection + memify staleness

**Goal:** The centrepiece feature working end to end, plus the staleness/memify pass.

**Build:**
- P1: Write `contradiction_detector.py` per `LLD.md` Section 3.4. Run Test Case 2 (true positive) and Test Case 3 (no false positive) back to back. Confirm the 0.7 confidence threshold behaves correctly on both.
- P2: Write `enrich_and_prune()` in `memory_store.py` using the confirmed `memify()` invocation from Day 1. Wire `post_ingest_pipeline()` per `LLD.md` Section 3.5. Run Test Case 4 — confirm what `memify()` actually returns/changes, log it in `BUILD_LOG.md`.
- Together: If `memify()` turns out to be unreliable or hard to get working in the time available, decide now whether to keep it minimal (call it, log the result, move on) rather than let it block Day 4 — contradiction detection matters more than a perfect staleness story.

**Deliverable:** Contradiction detection working, both test cases pass. `memify()` integrated, Test Case 4 result logged. This is the single most important day — do not compress it further if anything else slips.

---

### Day 4 — Jul 2 — Agent + full UI, built in parallel

**Goal:** LangGraph agent complete AND all 4 frontend screens built — same day, parallel tracks, not sequential.

**Why this works:** `API_CONTRACT.md` already defines every request/response shape. P1 can build the backend agent and routes against that contract while P2 builds the frontend against the same contract, without waiting on each other. This only works if neither side deviates from `API_CONTRACT.md` without updating it first and telling the other person immediately.

**Build:**
- P1 (backend): Finish `langgraph_agent.py` (`classify_intent`, `ingest_node`, `query_node`) per `LLD.md` Section 3.8. Write `answer_builder.py` per Section 3.6. Write `brief_generator.py` per Section 3.7. Expose all routes in `main.py` per `API_CONTRACT.md` — `/api/cases`, `/api/ingest`, `/api/query`, `/api/brief`, `/api/contradictions`, `/api/cases/:id/archive`.
- P2 (frontend): Scaffold Next.js project, connect `.env.local`. Build all 4 pages — `/ingest`, `/query`, `/contradictions`, `/brief` — plus `CaseSelector` in the navbar, all per `LLD.md` Section 5 and `API_CONTRACT.md`. Build against the contract even before the backend is finished — mock the responses locally if needed, then swap to real calls once P1's routes are live.
- Together, last 30 minutes: Connect frontend to the real backend. Run Test Case 5 (cross-session query) end to end through the actual UI, not just the CLI.

**Deliverable:** Full agent working end-to-end. All 4 frontend screens live against the real backend. This is the highest-risk day in the schedule — if it runs long, eat into Day 5's testing time rather than Day 3's contradiction work.

---

## Phase 2 — Test, Polish, Deploy, Submit (Days 5–6 · Jul 3–4)

### Day 5 — Jul 3 — Full test pass + Alibaba Cloud deployment + Cognee Cloud check-in

**Goal:** Every scenario in `TEST_CASES.md` verified. Backend deployed to Alibaba Cloud ECS.

**Build:**
- P1: Deploy backend to Alibaba Cloud ECS — SSH in, clone repo, install deps, set env vars, run with `uvicorn`. Confirm `/api/ingest` responds from the live IP. This is required for the Qwen submission regardless of the Cognee path taken.
- P2: Run all 7 `TEST_CASES.md` scenarios against the deployed/local app, end to end through the UI. Log any failures, fix what's fixable today, note what isn't for the README's "known limitations" if needed.
- Together: Check Cognee Cloud signup once more. If it's open now, decide together whether there's enough time left to migrate before Jul 5 (see `LLD.md` Section 10 checklist — budget at least half a day). If not enough time remains, commit to submitting on open-source `cognee` and move on — don't let this decision linger into Day 6.

**Deliverable:** All test cases verified or documented. Backend live on Alibaba Cloud. Migration decision made and recorded in `BUILD_LOG.md`.

---

### Day 6 — Jul 4/5 — Polish, demo video, architecture diagram, BOTH submissions

**Goal:** Submit to both hackathons. Cognee deadline is Jul 5 — do not let this slip.

**Build:**
- Together, early: Deploy frontend to Vercel pointing at the ECS backend. Confirm the full app works live, not just on localhost.
- Together: Export the architecture diagram from `HLD.md` Section 6 as a clean image.
- Together: Record the 3-minute demo video using `TEST_CASES.md` scenarios as the script:
  - 0:00–0:25 — the problem (a long deposition, the human memory limit)
  - 0:25–1:10 — ingest Test Cases 1–2, show contradiction detected live
  - 1:10–1:50 — restart/new session, ask the Test Case 5 question, get a sourced answer
  - 1:50–2:30 — ingest Test Case 4's correction, show the memify/staleness effect
  - 2:30–3:00 — generate the Test Case 6 brief, end on the architecture diagram
- P1: Write the README — clearly state which Cognee path was used (open-source or Cognee Cloud) and why, list the lifecycle operations used, link the demo video, embed the architecture diagram, disclose Claude/AI assistant usage per Cognee Rule 8.
- P2: Submit to the Cognee Hackathon — repo public, MIT license visible, track and prize category selected accurately based on the Day 5 migration decision.
- Together: If time remains same day, also complete the Qwen submission checklist (Alibaba Cloud deployment proof, architecture diagram, demo video link, track selection — Track 1 MemoryAgent). If not, finish Qwen submission Jul 6–9, well within its later deadline.

**Deliverable:** Cognee Hackathon submitted by Jul 5. Qwen Cloud Hackathon submitted by Jul 9 (can be finished in the days following Jul 5 if needed — only Cognee has the tight Jul 5 deadline within this 6-day window).

---

## Quick Reference — What's Due When

| Date | Milestone |
|---|---|
| Now – Jun 28 | Planning only. No code. |
| Jun 29 | Day 1 — Foundation, cognee API confirmed |
| Jun 30 | Day 2 — Extraction + memory pipeline |
| Jul 1 | Day 3 — Contradiction detection + memify (most important day) |
| Jul 2 | Day 4 — Agent + full UI, built in parallel (highest risk day) |
| Jul 3 | Day 5 — Full test pass + Alibaba Cloud deployment + Cognee Cloud check-in |
| **Jul 4–5** | **Day 6 — Polish, demo video, BOTH submissions; Cognee deadline is Jul 5** |
| Jul 6–9 | Slack buffer for finishing the Qwen submission if Day 6 ran out of time for it |

---

## If You Fall Behind

Priority order if time runs short — cut from the bottom, never the top:

1. **Contradiction detection (Day 3)** — the single most important feature for both hackathons. Never skip or rush this. If Day 3 runs long, borrow time from Day 4's UI polish, not from this.
2. **Extract → store → recall core loop (Day 2)** — nothing else works without this.
3. **LangGraph agent (Day 4, backend half)** — needed for both submissions to look like a real "agent." If parallel building with the frontend isn't working out, have P2 join P1 on this first, then both build UI together afterward with less time but more certainty.
4. **Cognee submission minimum viable (Day 6)** — can submit with a working backend + informal screen recording even if the polished frontend or demo video isn't fully ready. A real, working contradiction detector beats a beautiful UI with a broken backend.
5. **Alibaba Cloud deployment (Day 5)** — required for Qwen, not for Cognee. Since Qwen's deadline is Jul 9, this can slip into the Jul 6–9 buffer if absolutely necessary.
6. **Full 4-screen frontend (Day 4)** — if truly short on time, ship `/ingest` and `/query` first (the core loop), `/contradictions` and `/brief` second.
7. **Cognee Cloud migration** — only attempt if signup opens with comfortable time to spare (Day 5 check-in). Never let this delay the Day 5/6 submissions — submitting on open-source `cognee` is a completely valid fallback that still satisfies 5 of 6 judging criteria plus the general Cognee and Open Source prize tracks.
8. **Trial brief generator** — the most cuttable feature if truly out of time.

---

*Document owner: CourtMind Team · Last updated: planning phase, pre-Jun 29*
