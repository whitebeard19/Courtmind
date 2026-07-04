# CourtMind — Build Log (BUILD_LOG.md)

**Purpose:** This is the project's memory across AI sessions and across model switches. Every coding session, before doing anything else, read the latest entries here. At the end of every session, add a new entry. This is what makes switching between Claude, GPT, Gemini, or any other model safe — the next session reads this file and picks up exactly where the last one stopped.

---

## [Pre-build] — Planning Phase

**Worked on:** HLD v3.0/4.0, LLD v3.0/4.0, PROMPTS.md, CONTEXT.md, API_CONTRACT.md, TEST_CASES.md, PROGRESS.md, Roadmap.md — all written before any code, per Cognee Hackathon Rule 9 (no coding before June 29, 2026).

**Decisions made:**
- Architecture targets Cognee Cloud specifically
- Qwen2.5-72B via Qwen Cloud (DashScope) for all reasoning
- LangGraph orchestrates routing
- One Cognee Cloud dataset per legal case (`dataset_name = case_id`)
- Single codebase submitted to both hackathons

**Status at end of planning:** Nothing built yet — planning phase only.

---

## [June 29, 2026] — Session 1 (Day 1 Build)

**Worked on:** Full build — all backend files + complete Next.js frontend. Resolved all Cognee Cloud SDK questions by fetching live docs.

**Critical finding — Cognee Cloud SDK has changed:**

The old `cogwit-sdk` package documented in LLD.md v3.0/v4.0 is **superseded**. The current Cognee Cloud SDK uses the standard `cognee` pip package, not a separate `cogwit-sdk`. The connection pattern is:

```python
import cognee
await cognee.serve(url="https://your-tenant.aws.cognee.ai", api_key="your-key")
```

**Resolved SDK method mapping:**

| Old LLD assumption | Confirmed current API |
|---|---|
| `cogwit_instance.add(data, dataset_name)` | `await cognee.remember(text, dataset_name=name)` — ingest + graph build in one call |
| `cogwit_instance.cognify(dataset_ids=[...])` | Handled by `remember()` — or `await cognee.add()` + `cognify()` for low-level control |
| `cogwit_instance.search(query_text, query_type=CHUNKS)` | `await cognee.recall(query_text=query)` — auto-routes to best strategy |
| `cogwit_instance.search(query_text, query_type=GRAPH_COMPLETION)` | Same `cognee.recall()` — routing is automatic |
| `cogwit_instance.memify(dataset_ids=[...])` | `await cognee.improve(dataset_name=name)` — enrichment + staleness |
| Dataset deletion via `delete_dataset()` | `await cognee.forget(dataset_name=name)` |
| `pip install cogwit-sdk` | `pip install cognee` (same package used for local AND cloud — `serve()` switches mode) |
| Auth via `COGWIT_API_KEY` | Auth via `COGNEE_API_KEY` + `COGNEE_TENANT_URL` passed to `cognee.serve()` |

**Source:** https://docs.cognee.ai/cognee-cloud/connections/cloud-sdk (fetched live)

**Note on low-level ops:** `add()`, `cognify()`, `search()`, `memify()` still exist on the `cognee` module for fine-grained control. `remember()` and `recall()` are higher-level convenience wrappers. CourtMind uses the higher-level API but `memory_store.py` includes fallback checks for both.

**Environment variable changes from LLD:**
- OLD: `COGWIT_API_KEY`
- NEW: `COGNEE_API_KEY` + `COGNEE_TENANT_URL` (tenant URL required, not just key)
- `DASHSCOPE_API_KEY` unchanged

**Files built this session:**
- `backend/requirements.txt` — `cognee` package (not `cogwit-sdk`)
- `backend/cognee_config.py` — `connect_to_cloud()` via `cognee.serve()`
- `backend/memory_store.py` — ALL Cognee operations using new API
- `backend/qwen_client.py` — Qwen inference
- `backend/prompts.py` — all 6 prompts as constants
- `backend/extractor.py` — assertion extraction
- `backend/contradiction_detector.py` — Qwen contradiction judgment over Cognee candidates
- `backend/answer_builder.py` — Q&A synthesis
- `backend/brief_generator.py` — trial brief generation
- `backend/langgraph_agent.py` — LangGraph state machine
- `backend/main.py` — FastAPI routes (all 7 per API_CONTRACT.md)
- `frontend/` — complete Next.js 14 app (4 pages + CaseSelector + api.ts)
- `README.md` — hackathon submission document
- `.env.example` — updated with correct env var names

**Decisions made this session:**
- Used `cognee.remember()` (new high-level API) as primary op — cleaner than `add()` + `cognify()` separately
- Added `improve()` / `memify()` fallback in `enrich_and_prune()` for resilience across SDK versions
- Added `forget()` / `prune.prune_data()` fallback in `archive_case()` for same reason
- `recall()` used for both chunk-style and graph-completion retrieval — both use the same call, routing is automatic
- `_extract_text()` helper in `memory_store.py` handles defensive result parsing (dict vs attribute style)
- Contradiction storage uses `remember()` with structured text — "CONTRADICTION: 'A' contradicts 'B'..." — so future recall searches can find these by keyword
- `/api/contradictions` endpoint retrieves and parses stored contradiction strings from Cognee memory

**Broken / blocked:** Nothing broken. All files complete.

**Still to verify with live round trip on Day 2:**
1. Exact return type of `cognee.recall()` — whether results are dicts or objects, and which attribute holds text
2. Whether `cognee.improve()` accepts `dataset_name=` parameter or different signature
3. Whether `cognee.forget()` accepts `dataset_name=` or requires a different identifier
4. Whether `cognee.serve()` blocks or is async
5. Exact shape of `cognee.remember()` return value (if any)

**Next session should:**
1. Set COGNEE_API_KEY, COGNEE_TENANT_URL, DASHSCOPE_API_KEY in `.env`
2. Run a live round trip: `cognee.serve()` → `cognee.remember(test_text)` → `cognee.recall("test")` → log exact return shape in BUILD_LOG.md
3. Adjust `memory_store._extract_text()` if return shape differs from expected
4. Run TEST_CASES.md #1 (basic extraction) end to end via the /api/ingest endpoint
5. Run TEST_CASES.md #2 (contradiction detection) immediately after
6. Fix any discovered issues and re-test

---

## [June 29, 2026] — Session 2 (Day 1–3 verification + fixes)

**Worked on:** Empirically verified the cognee API against an actual install (Day 1's central open item), then fixed the bugs that verification surfaced. Set up the runnable environment.

**Environment setup:**
- Local default Python is 3.14 — **cognee does not support it**. Created a dedicated venv on Python 3.12: `backend/venv/` (py -3.12). Always run backend code through `backend/venv/Scripts/python.exe`.
- Installed `cognee` → resolved version **1.2.2**.
- Created `.env` at project root (gitignored). Keys left blank for the team to fill: `DASHSCOPE_API_KEY`, `COGNEE_API_KEY`, `COGNEE_TENANT_URL`.

**Cognee API — VERIFIED EMPIRICALLY (not from docs):**

Session 1's claim was correct. cognee 1.2.2 emits this on startup, confirming it:
> "Cognee 1.0 changes: New API → remember/recall/forget/improve (V1 add/cognify/search still work)."

All high-level methods exist: `serve`, `remember`, `recall`, `improve`, `forget`, `disconnect`. Confirmed real signatures via `inspect.signature`:

| Method | Real signature (key params) |
|---|---|
| `serve` | `serve(url=None, api_key=None, *, management_url=None, ...) -> CloudClient` |
| `remember` | `remember(data, dataset_name='main_dataset', *, session_id=None, self_improvement=True, ...) -> RememberResult` |
| `recall` | `recall(query_text, query_type=None, *, datasets=None, top_k=15, auto_route=True, ...) -> list[Response*Entry]` |
| `improve` | `improve(dataset='main_dataset', *, run_in_background=False, ...)` — **param is `dataset`, NOT `dataset_name`** |
| `forget` | `forget(*, data_id=None, dataset=None, dataset_id=None, everything=False, ...)` — **keyword-only, param is `dataset`** |
| `disconnect` | `disconnect(clear_saved=False)` |

**`recall()` return shape (verified via model_fields):** a list of typed Pydantic entries; the text lives in different fields per type:
- `ResponseGraphEntry` → `.text`
- `ResponseQAEntry` → `.answer`
- `ResponseGraphContextEntry` / `ResponseSessionContextEntry` → `.content`

`SearchType` members include `CHUNKS`, `GRAPH_COMPLETION`, `SUMMARIES`, `RAG_COMPLETION`, etc.

**Bugs found and fixed in `memory_store.py`:**
1. `enrich_and_prune()` called `improve(dataset_name=case_id)` — wrong kw; `dataset_name` fell into `**kwargs` and was silently ignored, so improve ran on the default dataset instead of the case. **Fixed → `improve(dataset=case_id)`.**
2. `archive_case()` called `forget(dataset_name=case_id)` — `forget` has no `**kwargs`, so this would raise `TypeError` at runtime. **Fixed → `forget(dataset=case_id)`.**
3. `recall_chunks()` / `recall_answer()` called `recall(query_text=...)` with **no dataset scoping** — searched across ALL cases (cross-case contamination). **Fixed → both now pass `datasets=[case_id]`.** `recall_chunks` additionally now requests `query_type=SearchType.CHUNKS, auto_route=False` so contradiction detection gets individual stored assertions to compare, not a single synthesised answer.
4. `_extract_text()` only handled `.text` / `.search_result` — would have missed `.answer` and `.content`, dumping raw object reprs into Qwen. **Fixed → now checks `.text` / `.answer` / `.content` (and dict equivalents) in priority order.**

**Qwen model — VERIFIED LIVE (Day 1 test result):**
- The key is an **international (Singapore)** DashScope key → works on `https://dashscope-intl.aliyuncs.com/...`, returns 401 on the China endpoint. Endpoint is correct.
- `qwen2.5-72b-instruct` (the model the LLD/code originally hardcoded) returns **403 access_denied** — that open-source-named model is NOT enabled for this account on the intl region.
- `qwen-plus`, `qwen-turbo`, `qwen-max` all work. **Switched `qwen_client.py` to env-configurable `QWEN_MODEL`, default `qwen-plus`.** Day 1 Qwen test (basic + JSON mode + intent classification) all pass on qwen-plus.

**Cognee recall return shape — VERIFIED LIVE:** `recall()` returns a `list[dict]` (plain dicts, not Pydantic objects) with keys `kind, search_type, text, score, dataset_id, dataset_name, metadata, raw, structured, source`. Text is in `['text']`. `_extract_text()`'s dict branch handles this. Default `recall()` (no query_type) auto-routes to `GRAPH_COMPLETION` and returns a *synthesised* answer per dataset — confirming why `recall_chunks` must pass `query_type=SearchType.CHUNKS` for contradiction candidates. `remember()` of one sentence took ~16s (self_improvement on by default) — watch ingest latency in the demo.

**Live pipeline run (test_full_pipeline) — RESULT:** extraction ✅, query ✅, brief ✅ (brief even surfaced the Mar 12 vs Mar 14 conflict), but **live contradiction detection at ingest found 0** — the centerpiece. Root-caused via isolated debug scripts:

- cognee 1.x ships **conversational session memory ON by default**. `remember()` treats inputs as chat turns; `recall()` returns chat-style replies ("Got it, thank you...") instead of stored facts.
- Retrieval must use `cognee.search(query_type=SearchType.CHUNKS, datasets=[case_id])`, NOT `recall()`. Cloud `search()` wraps results per dataset: `[{dataset_id, dataset_name, search_result: [chunk,...]}]`; chunks are dicts with a `text` field. **Switched `recall_chunks`/`recall_answer` to `search()` + a `_flatten_search()` helper.**
- **`search()` is query-sensitive (verified):** a *topical noun-phrase* query (`"quarterly review meeting"`) reliably returns the real chunks; a *verbatim full sentence* or *vague* query (`"meeting"`) returns a conversational `str` instead. Fixes applied: (a) `_flatten_search()` now **drops plain-string results** (keeps only dict chunks), (b) the contradiction pass now queries with a **topical query built from the assertion's entities** (`_topical_query()` in `contradiction_detector.py`), not the verbatim sentence.
- `CACHING=false` env added (disables session memory locally) — set before `import cognee` in `cognee_config.py` and in `.env`. NOTE: in cloud mode session behavior is partly server-side, so the str-filter + topical-query fix is what actually guarantees correctness.
- Also seen: `forget()` immediately followed by `remember()` on the same dataset → **409 ProgrammingError** (deletion is async). Don't re-ingest into a just-forgotten dataset without a delay.

**CONFIRMED WORKING (re-run of test_full_pipeline):** Test Case 1 (extraction) ✅, Test Case 2 (contradiction) ✅ — contradiction detected, **confidence 1.0** (Mar 12 vs Mar 14), Query ✅.

**Final write-path decision — switched remember() → add() + cognify():** `store_assertion()` and `store_contradiction()` now use `cognee.add(text, dataset_name=case_id)` + `cognee.cognify(datasets=[case_id])` instead of `remember()`. This is the pure document-graph path with **no conversational session layer**, which is what made contradiction candidates retrieve reliably. Combined with: (a) topical-query retrieval (`_topical_query()`), (b) `_flatten_search()` dropping conversational string results, (c) `detect_contradictions()` stripping the `[Speaker:...]` metadata off candidate text before Qwen comparison and for self-comparison skipping.

**TWO KNOWN ISSUES still open after this run:**
1. **`GET /api/contradictions` returns 0** even though 4 contradictions were detected and stored during ingest (Step 6 of the pipeline test). The endpoint retrieves stored `CONTRADICTION:` chunks via a semantic query that isn't reliably surfacing them. The contradictions ARE returned correctly in the `/api/ingest` response — it's only the separate retrieval endpoint (which the frontend `/contradictions` page uses) that comes back empty. Fix options: cache detected contradictions in an in-memory per-case registry in `main.py` (like `cases`), and/or query the contradiction records with a more reliable filter.
2. **Brief generation JSON parse failure** (Step 7): `infer()` in `qwen_client.py` caps `max_tokens=1000`; a 500-word structured brief can exceed that and get truncated → invalid JSON → `brief_generator` falls back to its error stub. Fix: raise `max_tokens` for the brief call (or make it a per-call arg), and/or strip markdown code fences before `json.loads`.

**BOTH KNOWN ISSUES FIXED + CONFIRMED (re-run of test_full_pipeline):** Step 6 `/api/contradictions` → 4 contradictions; Step 7 brief → real summary (3 contradictions, 5 key assertions). Fixes: (1) added in-memory `contradictions_by_case` registry in `main.py`, populated on `/api/ingest`, served first with Cognee parse as cross-session fallback; (2) `qwen_client.infer()` now takes `max_tokens` (brief uses 3000, answer uses 1500) + `brief_generator` strips code fences before `json.loads`.

**INGEST LATENCY OPTIMIZATION (was ~68–72s/document):** The cost was `cognify()` running once per assertion and `improve()` once per assertion. Refactored to call the expensive cloud ops ONCE per document:
- `memory_store.store_assertion()` / `store_contradiction()` now **add() only** (no cognify). New `memory_store.build_graph(case_id)` does the single `cognify()`.
- `contradiction_detector.find_contradictions()` is the new side-effect-free check (recall + Qwen judgment, no writes). `run_full_contradiction_pass()` kept self-consistent for standalone use.
- `langgraph_agent.ingest_node()` restructured: stage all assertions → `build_graph()` once → judge contradictions → stage all contradictions → `build_graph()` once → `improve()` once.
- `classify_intent()` now **skips the Qwen call when the route already set a concrete intent** (the `/api/ingest` path), removing a wasted round trip + misclassification risk.
- Expected ingest: roughly **2 cognify + 1 improve per document** instead of ~4 cognify + 4 improve. (Pending live confirmation of the new wall-clock time after backend restart.)

**Backend readiness audit (structural, no network):** all modules import, agent compiles, all routes present (`/api/cases` GET+POST, `/api/ingest`, `/api/query`, `/api/brief`, `/api/contradictions`, `/api/cases/{id}/archive`), batched memory API + contradiction registry verified. NOT yet exercised live: `PATCH /api/cases/{id}/archive` (forget), TEST_CASES #4/#5/#6/#7.

**REGRESSION after latency batching — root-caused & fixed (cold-search retry):** After batching cognify/improve, contradiction detection intermittently returned 0 again. Diagnosed: the **same** CHUNKS query returned **0 results on the first call and 6 on the immediate next call** — Cognee Cloud `search()` has an eventual-consistency / cold-first-query window. The old per-assertion code made so many cognify/improve/recall calls that search was always warm by the time it mattered; batching removed that incidental warm-up, so the contradiction recall now lands on the cold query. **Fix:** `memory_store._search_chunks()` retries on empty results (5 attempts, 2s apart) before giving up; `recall_chunks`/`recall_answer` go through it. Validated: recall returns all 6 chunks, `detect_contradictions` finds 4. A genuinely empty dataset just costs a few extra seconds.

**TIMEOUT after retry fix — fixed by one-recall-per-ingest:** The retry-on-empty (5×2s) combined with one recall *per assertion* made TC1 ingest (4 assertions) exceed the test client's 120s read timeout (each cold recall ≈ 5 sleeps + network ≈ 18s, ×4 ≈ 70s on top of ~24 Qwen judgment calls). Fix: `ingest_node` now does **ONE recall per document** — `_pool_query()` unions all assertions' entities into a single topical query, recalls the candidate pool once (top_k=20), and reuses it for every assertion's `detect_contradictions()`. So the costly cold-retry window is paid at most once per ingest, not N times. Also more correct (every assertion judged against the same full pool). `find_contradictions()` remains for standalone use; `ingest_node` now imports `detect_contradictions` directly.

**Option B verification (TC5/TC7/archive) — ALL PASS:**
- **TC5 cross-session ✅** — a fresh process (separate from the server that ingested) queried case `094ede52` via `answer_builder.build_answer` and got a sourced, contradiction-aware answer (cites Martinez/Mar-12 with sources [1][2][3][5][8]; flags Chen/Mar-14 conflict). Proves Cognee persistence survives across sessions — the Track 1 MemoryAgent core.
- **TC7 empty edge ✅** — single isolated doc → 1 assertion, 0 contradictions, no fatal error.
- **Archive ✅** — `forget(dataset=case)` returns without error.

**KNOWN NON-BLOCKING ISSUE — `improve()` 404 on fresh datasets:** `enrich_and_prune()` → `cognee.improve(dataset=case_id)` returns `404 {"detail":"Not Found"}` for newly-created datasets. It's caught (non-fatal); ingest, contradiction detection, query, and brief all work without it. Impact: the staleness/memify feature (TEST_CASE #4) is not functioning. Per roadmap this is the lowest-priority / most-cuttable feature, so deferred. TODO if revisited: confirm whether cloud `improve` needs `dataset_id` (UUID) rather than `dataset` (name), or a minimum corpus size.

## [June 30, 2026] — Session 3 (frontend integration: reliability hardening + Cognee budget)

**Symptom from live UI:** contradictions not found + `/api/contradictions` timing out.

**ROOT CAUSE #1 — Cognee Cloud budget exhausted.** `cognify()` started returning
`500 litellm.RateLimitError: Budget has been exceeded! Current cost: 2.50, Max budget: 2.5`.
All prior testing consumed the **$2.50** free budget. Worse, the failing `cognify` **retried
server-side for ~275s** before erroring — that long block was the UI "timeout." **ACTION
REQUIRED (user):** restore/raise Cognee Cloud budget in the dashboard (`.env.example` notes
promo code **COGNEE-35** = $35 credit). Until then, anything needing `cognify` (graph build,
query, brief, cross-session search) is degraded.

**ROOT CAUSE #2 — contradiction detection was coupled to Cognee.** It depended on Cognee
`search()` for candidates (flaky cold window) and the whole ingest aborted if `cognify`
threw. Fixed by decoupling:

1. **Write-through assertion cache** (`memory_store._assertion_cache`): every stored
   assertion is mirrored in memory, keyed by case_id. `ingest_node` now builds the
   contradiction candidate pool from `get_cached_assertions()` — instant, 100% reliable,
   **no Cognee search at ingest time**. Cognee still persists everything (add+cognify) and
   powers query/brief/cross-session; the cache is just a fast working set. Cache is
   populated BEFORE the cloud `add()` so it survives an `add()` failure; cleared on archive.
2. **`build_graph()` is now best-effort + time-bounded** (`asyncio.wait_for`, 45s, never
   raises). A hung/failing `cognify` can no longer block ingest for minutes or abort it.
3. **`ingest_node` restructured** so every Cognee op (`add`, `cognify`, `improve`) is caught
   individually and is non-fatal. Contradiction detection (Qwen + cache) runs regardless of
   Cognee health. Removed the now-unused `_pool_query`.
4. **`/api/contradictions` no longer hangs**: serves the in-memory `contradictions_by_case`
   registry first; the Cognee fallback now uses `recall_chunks(..., retries=1)` (single fast
   attempt) so the GET can't stall on the cold-search retry window.

Net effect: **contradiction detection (the centerpiece) now works even with Cognee's budget
exhausted** — it only needs Qwen (separate DashScope budget) + the cache. Query/brief/persistence
need Cognee budget restored to be fully healthy.

**Latency hardening for `cognify`:**
- `build_graph()` now calls `cognify(datasets=[...], run_in_background=True)` (submit-and-return)
  with a 30s `wait_for` safety bound. Cut Doc-1 ingest from ~52s → **~5.6s** on the over-budget
  tenant. Dropped the redundant **second** `cognify` per ingest (after staging contradictions).
- Caveat: on a budget-exhausted/unhealthy tenant, `cognify` still occasionally blocks ~9 min
  (observed 535s on Doc 2). `asyncio.wait_for` can't cancel cognify's internal blocking call,
  so the only real fix is a healthy tenant. With budget restored, cognify returns in ~15s and
  ingest is back to ~5–60s. (Contradiction detection is unaffected either way — cache + Qwen.)

**New Cognee tenant + `.env` hardening:** user swapped to a fresh Cognee tenant/API key
(`tenant-778555d6...`) — likely to get fresh budget. The `.env` had a **leading space** in
`COGNEE_TENANT_URL`; `cognee_config.py` now `.strip()`s `COGNEE_API_KEY` and `COGNEE_TENANT_URL`
so stray whitespace can't break the connection. Next: user restarts backend with new creds and
re-tests in the UI.

**Precision/display fixes from live-UI review (4 bugs, all unit-verified):**
1. **False positive on sequential timestamps** (e.g. "arrived 2:00 PM" vs "left 3:15 PM" flagged as contradiction). Fix: `CONTRADICTION_PROMPT` now has an explicit sequential-events rule + negative examples; differing times only contradict when describing the SAME event.
2. **`reason` text disagreed with `contradicts` boolean** (reason said "do not strictly contradict" but boolean was true @ 0.85). Fix: (a) prompt reordered so `reason` is emitted BEFORE `contradicts` (commit to reasoning first) with an explicit consistency rule; (b) code guard `_reason_supports_contradiction()` in `contradiction_detector.py` drops any result whose reason hedges ("do not contradict", "can both be true", "compatible", "sequential events", …) regardless of the boolean.
3. **Ingestion metadata tags leaking into displayed text** — `[Speaker:…][Date:…][Source:…]` showed in contradiction cards (assertion_b). Fix: `_clean_text()` (regex) strips tags; `detect_contradictions` now stores/returns CLEAN `assertion_a`/`assertion_b` (and compares clean text). Registry + stored CONTRADICTION strings are now tag-free.
4. **Too many redundant contradictions** flooding the UI. Fix: `dedupe_contradictions()` collapses by normalized `assertion_b`, keeping highest confidence, sorted desc; applied in `ingest_node`.

Also removed the `improve()`/staleness call from ingest (404s on this tenant, lowest priority) and added on-disk persistence (`backend/.courtmind_state.json`) so cases/contradictions/assertion-cache survive backend restarts & hot-reloads (fixes "can't select the case" after a reload). Run uvicorn WITHOUT `--reload` during demos.

**RECALL GAP fixed — detection was running AFTER cognify.** Live *Reyes v. Vanguard* test
caught 2 of 4 expected contradictions; the warning-sign and Whitfield self-correction were
missed. Diagnosed: both pairs return `contradicts=true @0.95, guard_ok=true` when tested
directly — so the detector/guard are correct. Root cause: `ingest_node` ran `build_graph()`
(cognify) BEFORE contradiction detection, and when cognify hangs (over-budget/slow tenant),
detection for that document never ran → 0 contradictions for that doc (Doc 3 didn't hang →
caught; Docs 2 & 4 hung → missed). **Fix: reordered `ingest_node` so detection (cache-based,
independent of the graph) runs FIRST, then `store_contradiction`, then `schedule_build_graph()`
FIRE-AND-FORGET** (`memory_store.schedule_build_graph` → `loop.create_task`) so cognify can
never block the response or skip detection. Ingest now returns as soon as contradictions are
found; the graph builds in the background for query/brief.

## [July 1, 2026] — Session 4 (Cognee-forward refactor for "best use of Cognee Cloud")

**Motivation:** the Cognee prize rewards best use of the flagship lifecycle (`remember`/`recall`/
`improve`/`forget`). We were only using `forget()` (+ low-level `add`/`cognify`/`search`).

**Lifecycle verification on the live cloud tenant:**
| Op | Result |
|---|---|
| `remember(text, dataset_name=case)` | ✅ works, ~6–11s |
| `recall(query_text, datasets=[case])` | ✅ works great — graph-completion answer that itself surfaces the conflicting facts |
| `forget(dataset=case)` | ✅ works (`status: success`) |
| `improve(dataset=case)` | ❌ 404 — endpoint gated on this tenant/plan (fails even on remember()-created data, so NOT a data-path issue) |
| `memify(dataset=case)` | ❌ 422 LLMAPIKeyNotSet — runs client-side, needs a local LLM key configured |

**Refactor applied (memory_store.py):**
- `store_assertion()` / `store_contradiction()` now persist via **`cognee.remember()`** (fire-and-forget
  `schedule_remember()`), replacing `add()`+`cognify()`. The write-through cache still feeds contradiction
  detection, so it stays instant and independent of Cognee latency.
- `recall_answer()` now uses **`cognee.recall()`** (auto-routed semantic + graph traversal) with a
  raw-CHUNKS `search()` fallback for a cold graph. Powers the Q&A screen.
- `forget()` unchanged (archive). Enrichment (`improve`/`memify`) left wired but not called — plan-gated
  (see table); disclosed honestly rather than faked.
- Removed the separate `build_graph`/cognify step from ingest (remember() structures the graph).

**Validated end-to-end:** ingest via remember() (7s & 11s — faster than the old ~40–60s), contradiction
detection still PASS (2 found, clean text, correct confidence), and recall()-based Q&A returns a
contradiction-aware answer. Net: **1/4 → 3/4 flagship ops genuinely used**, ingest faster, no regression.

**improve()/memify() — FINAL determination (unusable from this environment):**
- Tenant API (`tenant-…aws.cognee.ai`) exposes `remember`/`recall`/`forget`/`add`/`cognify`/`update`/
  `search`/`visualize` but **NOT `/improve`** → SDK `cognee.improve()` 404s. (User confirmed via the
  tenant's OpenAPI listing.)
- The real `improve`/`memify` REST endpoints live on the central host **`https://api.cognee.ai`** (per
  Cognee's curl docs), authenticated with the raw API key as `Bearer`. But `api.cognee.ai` is
  **unreachable from this network** — plain `GET /health` fails at the TLS handshake
  (`TLSV1_ALERT_INTERNAL_ERROR`) via both httpx and aiohttp = server/WAF geo-block, not auth.
- `memify()` locally = needs local LLM (configurable) + hits a `text-embedding-v3` tiktoken tokenizer
  mismatch = rabbit hole.
- `visualize_graph()` SDK doesn't forward `dataset` to the cloud → 422 under access control.
- **Decision:** ship with `remember` + `recall` + `forget` (3/4 flagship ops, all real tenant endpoints).
  Enrichment (`improve`/`memify`) disclosed honestly as tenant/network-gated. **Retry direct-REST
  `improve` from the deployed Alibaba ECS box** (different network) as a possible bonus post-deploy.

## [July 1, 2026] — Session 5 (pipeline reliability hardening)

Fixed the write-race debt introduced by fire-and-forget `remember()`:

1. **Per-case write serialization** — `schedule_remember()` now runs each write under a
   per-case `asyncio.Lock` (`_serialized_remember`), so concurrent `remember()` calls to the
   same (possibly new) dataset can't race on dataset creation (the 409 ProgrammingError) or
   produce unstable graph state.
2. **Flush-before-read** — new `flush_writes(case_id)` awaits all pending writes for a case
   (bounded 90s). `recall_answer()` and `recall_chunks()` flush first, so query/brief never
   recall a half-written memory. Validated: ingest → immediate query flushed 3 pending writes
   (~39s) and returned a correct, sourced, contradiction-aware answer.
3. **No fake-success** — `answer_builder.build_answer()` no longer returns HTTP 200 with a
   "Memory retrieval failed" body. A genuine retrieval/synthesis error now RAISES → `/api/query`
   returns 500. An empty case returns a clear "No memory found yet" 200 (not a failure).
4. **Stronger query fallback** — `recall_answer()` flushes, tries `recall()`, and on error OR
   empty falls back to a retrying CHUNKS `search()`; only raises if both fail.
5. **Strict pipeline test** — `test_full_pipeline.py` `_query_looks_valid()` fails the query
   step unless the answer is substantive and memory-backed (non-empty, has sources, not a
   failure message). Test runner forces `PYTHONIOENCODING=utf-8` (Windows-safe, ASCII markers).
6. **Mojibake cleanup** — `memory_store.py` had 38 garbled comment/docstring characters
   (UTF-8/cp1252 mismatch); fixed with `ftfy` + ASCII separators; stale add/cognify docstrings
   updated to the current remember()-based reality. 0 residual.

**Day 3 status:** Contradiction detection (`contradiction_detector.py`) and the memify/staleness pass (`enrich_and_prune` via `improve()`) were already written in Session 1 and now call the correct, verified API. Cloud connection via `serve()` means cognee handles the LLM + embeddings server-side, so no local LLM/embedding config is needed for the cloud path.

**Not yet done (needs API keys — team to run):**
- Live round trip + all TEST_CASES. See "How to test" in PROGRESS.md / the run commands below.

**Open question for live testing:** confirm `recall(query_type=SearchType.CHUNKS, auto_route=False)` returns multiple distinct chunk entries (needed for contradiction candidates). If auto_route override behaves unexpectedly, fall back to the low-level `search(query_text, SearchType.CHUNKS, datasets=[case_id], top_k=...)`.

---

*This file grows with every session. Never delete old entries — they are the project's history and prevent re-litigating already-settled decisions.*
