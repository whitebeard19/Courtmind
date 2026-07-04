# CourtMind — Test Cases (TEST_CASES.md)

**Version:** 3.0 — Cognee Cloud + Qwen architecture

**Purpose:** Concrete, reusable test inputs so every AI session and every model tests against the same fixtures instead of inventing new ones each time. This also doubles as the script for your demo video.

---

## Test Case 1 — Basic Extraction

**Use for:** verifying `extractor.py` works at all

**Input document** (`source_label`: "Martinez Deposition p.1", `speaker`: "John Martinez"):
```
I attended the quarterly review meeting on Tuesday, March 12, 2024. The meeting
took place at the downtown office on Fifth Street. I signed the updated vendor
contract at the end of the meeting. Sarah Chen was also present.
```

**Expected extraction (approximate, exact wording may vary):**
- Martinez attended the quarterly review meeting on March 12, 2024
- The meeting took place at the downtown office on Fifth Street
- Martinez signed the updated vendor contract at the end of the meeting
- Sarah Chen was present at the meeting

**Pass criteria:** 4 distinct assertions extracted, each tagged with speaker "John Martinez" where appropriate, date "2024-03-12" captured correctly.

---

## Test Case 2 — Direct Contradiction (date conflict)

**Use for:** verifying `contradiction_detector.py` — this is the centrepiece feature, test it thoroughly

**Document A** (`source_label`: "Martinez Deposition p.1", `speaker`: "John Martinez"):
```
The quarterly review meeting took place on Tuesday, March 12, 2024.
```

**Document B** (`source_label`: "Chen Statement", `speaker`: "Sarah Chen"):
```
The quarterly review meeting was held on Thursday, March 14, 2024.
```

**Expected result:** Ingesting Document B after Document A should produce a contradiction with `confidence >= 0.85` and a reason referencing the conflicting dates (Tuesday March 12 vs Thursday March 14).

**Pass criteria:** Contradiction detected, confidence above threshold (0.7), reason text clearly explains the date conflict.

---

## Test Case 3 — Non-Contradiction (related but compatible facts)

**Use for:** verifying the contradiction detector does NOT produce false positives

**Document A:**
```
John Martinez attended the meeting on March 12, 2024.
```

**Document B:**
```
Sarah Chen also attended the meeting on March 12, 2024.
```

**Expected result:** No contradiction. Both statements can be true simultaneously — two different people attending the same meeting.

**Pass criteria:** `contradicts: false` or confidence well below 0.7 if any borderline result appears.

---

## Test Case 4 — Staleness / Updated Information

**Use for:** verifying the staleness/reliability signal feeding into Cognee Cloud's memify() enrichment step

**Document A** (`speaker`: "John Martinez", ingested first):
```
The meeting was scheduled for Tuesday, March 12, 2024.
```

**Document B** (`speaker`: "John Martinez", ingested second — same speaker, corrected account):
```
Correction to my earlier statement: the meeting was actually rescheduled to
Thursday, March 14, 2024, due to a venue conflict.
```

**Expected result:** Document A's assertion about "Tuesday March 12" should be flagged as stale/unreliable once Document B is ingested, since it's the same speaker actively correcting themselves.

**Pass criteria:** Whatever mechanism is confirmed in `BUILD_LOG.md` for surfacing staleness (score, flag, deprioritised ranking) should visibly treat Document A's claim differently after Document B is ingested, compared to before.

---

## Test Case 5 — Cross-Session Query

**Use for:** verifying persistent memory survives a new session — this is the Track 1 MemoryAgent and Cognee core requirement

**Steps:**
1. Ingest Test Case 1 and Test Case 2's documents (both A and B) into the same case.
2. Fully restart the backend process (or at minimum, start a completely new request context with no shared in-memory state).
3. Query: `"What did Martinez say about the meeting date?"`

**Expected result:** The answer correctly cites Martinez's claim (Tuesday March 12), correctly references the source document, and explicitly mentions the contradiction with Chen's statement (Thursday March 14).

**Pass criteria:** Answer is accurate, sourced, and contradiction-aware, despite coming from a fresh process/session with no shared memory other than what's in Cognee.

---

## Test Case 6 — Trial Brief Generation

**Use for:** verifying `brief_generator.py`

**Setup:** Ingest Test Cases 1, 2, and 4's documents into one case named "Test Case Alpha."

**Request:** Generate a brief with `max_words: 500`.

**Pass criteria:**
- `top_contradictions` includes the Tuesday/Thursday date conflict with severity "high" or "medium"
- `brief_summary` is under 80 words and accurately reflects the state of the case memory
- Output is valid JSON matching the exact schema in `PROMPTS.md` Prompt 6

---

## Test Case 7 — Empty / No Contradictions Edge Case

**Use for:** verifying nothing breaks when there's nothing interesting to find

**Input:** A single, isolated document with no related prior context in the case.
```
The contract renewal date is set for January 1, 2025.
```

**Pass criteria:** Extraction succeeds, zero contradictions found, no errors thrown, response shape still matches `API_CONTRACT.md` exactly (`contradictions_found: 0`, `contradictions: []`).

---

## How to Use These During Build

- Run Test Case 1 immediately after building `extractor.py` (Day 2 of build per roadmap).
- Run Test Cases 2 and 3 together immediately after building `contradiction_detector.py` (Day 4) — testing both the true positive and the false positive guard in the same session catches threshold issues early.
- Run Test Case 4 once `memify()`'s real behaviour is confirmed (Day 5).
- Run Test Case 5 once the full LangGraph agent is wired (Day 6) — this is the single most important test for both hackathons' judging criteria.
- Run Test Case 6 once `brief_generator.py` exists.
- Run Test Case 7 anytime — good smoke test after any refactor.

These same documents and questions are reusable directly in the demo video script.
