# CourtMind — Demo Guide

A ready-to-film case that shows CourtMind at maximum potential: **four different kinds of contradiction, a precision "no false positive" moment, cross-session persistence, sourced Q&A, and a trial brief** — in one coherent story a non-lawyer instantly understands.

---

## The case: *Reyes v. Vanguard Logistics*

A warehouse worker, **Daniel Reyes**, is injured when a forklift skids on a wet floor. He sues the operator, **Vanguard Logistics**, for negligence. Three people give accounts — Reyes, the shift supervisor **Marcus Whitfield**, and the safety inspector **Elena Okafor** — plus a contract/records document. Their stories don't line up. CourtMind finds exactly where.

### Documents to ingest (in order)

**Document 1** — Source: `Reyes Deposition p.1` · Speaker: `Daniel Reyes`
```
On September 14, 2024, I was operating forklift number 7 in dock area B. The floor near bay 3 was wet and there was no warning sign posted anywhere. My shift started at 7:00 AM that morning. The incident happened at around 2:30 PM when the forklift skidded on the wet floor.
```

**Document 2** — Source: `Incident Report - Initial` · Speaker: `Marcus Whitfield`
```
A wet-floor warning sign was posted near bay 3 at the start of the shift. The dock safety inspection was completed on September 12, 2024, two days before the incident. I was on the warehouse floor when the incident occurred at 2:30 PM. Elena Okafor inspected and cleared forklift number 7 that morning.
```

**Document 3** — Source: `Okafor Statement` · Speaker: `Elena Okafor`
```
I am the safety inspector for the facility. I completed the dock safety inspection on September 14, 2024, the same day as the incident. I never inspected forklift number 7 at any point. The delivery truck from Meridian Freight arrived at the dock at 2:00 PM.
```

**Document 4** — Source: `Whitfield Supplemental Statement` · Speaker: `Marcus Whitfield`
```
Correction to my earlier statement: I was actually in the supervisor's office, not on the warehouse floor, when the incident occurred. Daniel Reyes left the loading dock at approximately 3:15 PM after the incident was documented.
```

### What CourtMind catches (the payoff)

Four contradictions, of four different types — this is the "maximum potential" spread:
1. **Missing-vs-present fact** — Reyes: *"no warning sign"* vs Whitfield: *"a wet-floor sign was posted."*
2. **Conflicting dates** — Whitfield: inspection *"completed Sept 12"* vs Okafor: *"completed Sept 14."*
3. **Direct denial** — Whitfield: *"Okafor inspected and cleared forklift #7"* vs Okafor: *"I never inspected forklift #7."*
4. **Witness self-correction** — Whitfield initial: *"on the warehouse floor"* vs his own supplement: *"in the supervisor's office."*

And the precision moment — CourtMind does **NOT** flag these (proving it isn't just keyword-matching timestamps):
- Truck *"arrived at 2:00 PM"* vs Reyes *"left at 3:15 PM"* — sequential events, not a conflict.
- *"shift started 7:00 AM"* vs *"incident at 2:30 PM"* — sequential, not a conflict.

---

## 3-minute video script

> **Prep before recording (important):** Ingest all four documents *before* you hit record, then create a *second* fresh case to ingest live on camera. Ingest/query have real latency (LLM + cloud memory); you want the "already loaded" case ready for the query/brief/contradiction-map beats, and only ingest 1–2 docs live for the reveal. Never ingest-then-immediately-query on camera — query a case whose writes have already drained (it's instant then).

**0:00–0:20 — The problem (hook)**
> "A single lawsuit can hold thousands of pages of testimony. The fact that wins the case is often a *contradiction* — one witness says the opposite of another, weeks apart. No human reliably catches them. CourtMind does — because it never forgets."

**0:20–1:20 — Ingest & the live reveal**
- Show the Ingest screen. Paste **Document 2** (Whitfield). Ingest — assertions appear.
- Paste **Document 3** (Okafor). Ingest — and **a contradiction pops up live**: *"Okafor inspected and cleared forklift #7"* vs *"I never inspected forklift #7,"* 100% confidence, with a plain-English reason.
> "The moment a new statement conflicts with anything already in memory, CourtMind flags it — with the two statements, a reason, and a confidence score."

**1:20–2:00 — The Contradiction Map (breadth + precision)**
- Switch to the already-loaded case → **Contradictions** screen. Scroll the four contradictions.
> "Across the full case it's found four conflicts — a missing safety sign, two different inspection dates, a flat denial, and a witness who corrected his own account."
- Point out what's *absent*: "Notice the truck arriving at 2 PM and Reyes leaving at 3:15 aren't flagged — arrival before departure is normal. CourtMind reasons about events, it doesn't just match timestamps."

**2:00–2:35 — Cross-session Q&A (the memory proof)**
- Go to **Query**. Ask: *"When was the safety inspection completed?"*
> "And because the memory is persistent — this works even after the server restarts — I can just ask."
- Read the sourced, contradiction-aware answer (cites both dates and the conflict).

**2:35–3:00 — The brief + close**
- Go to **Brief** → Generate. Show the executive summary, ranked contradictions with recommended actions.
> "In one click, a trial-prep brief: the case's contradictions ranked, with recommended next steps. CourtMind is built on Cognee Cloud's memory graph and Qwen's reasoning — the memory that remembers the one fact that can't be true."

---

## How to test it yourself (quick checklist)

1. Create a case → **Reyes v. Vanguard Logistics**.
2. Ingest Documents 1→4 in order (wait for each to finish).
3. **Contradictions** screen shows 4 contradictions; none of the sequential-event pairs.
4. **Query** each of:
   - *"When was the safety inspection completed?"* → surfaces Sept 12 vs Sept 14.
   - *"Was a warning sign posted near bay 3?"* → Reyes vs Whitfield conflict.
   - *"Did Okafor inspect forklift number 7?"* → the denial conflict.
   - *"Where was Whitfield when the incident occurred?"* → his self-correction.
5. **Brief** → Generate → expect the inspection-date, warning-sign, and forklift-inspection conflicts as top items.

**Cross-session proof (great for the video):** after ingesting, restart the backend, then run a Query on the same case — it still answers from Cognee memory. (On the deployed app, just come back later; the graph persists in Cognee Cloud.)
