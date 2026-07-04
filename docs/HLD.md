# CourtMind — High Level Design (HLD)

**Version:** 4.0 — Cognee (open-source, build now) → Cognee Cloud (migrate if access opens) + Qwen  
**Date:** June 2026  
**Submissions:** Cognee Hackathon, "The Hangover Part AI" by WeMakeDevs (Jun 29 – Jul 5, 2026) · Qwen Cloud Global AI Hackathon Track 1 — MemoryAgent (deadline Jul 9, 2026)  
**Build window:** June 29 – Jul 2 build · Jul 3–4 test/polish · Jul 5–6 submit both (6-day compressed plan — see `Roadmap.md`)  
**Target prize:** Best Use of Cognee Cloud (Apple iPhone 17) if migration completes in time; otherwise Best Use of Open Source / general Best Use of Cognee — see Section 3

---

## 1. Executive Summary

CourtMind is an AI-powered litigation memory assistant that gives lawyers persistent, cross-session memory across all case documents. It ingests depositions, witness statements, contracts, and emails — extracts structured assertions — and automatically detects contradictions between them.

This architecture uses **Cognee** as the project's core memory substrate. The build currently targets the **open-source `cognee` package** (self-hosted, no signup required) because **Cognee Cloud's signup is currently at capacity** and many participants cannot create accounts. The codebase isolates every Cognee call inside one module (`memory_store.py`), so migrating to **Cognee Cloud** (via `cogwit-sdk`) — which would make the project eligible for the iPhone 17 "Best Use of Cognee Cloud" prize, distinct from the "Best Use of Open Source" prize — is a contained, single-file change if signup access opens before the submission deadline. See Section 3 for the full strategy and `LLD.md` Section 0 for the technical detail.

**Qwen2.5-72B** (via Qwen Cloud) provides the reasoning layer on top: extraction, contradiction detection, staleness judgment, and answer synthesis. This single codebase is submitted to both hackathons.

---

## 2. Problem Statement

Litigation is one of the most memory-intensive professions on earth. A litigator juggling multiple active cases reads thousands of pages of depositions, interviews dozens of witnesses, and must track — across months — who said what, who contradicted whom, and which exhibit proves which point.

Today this is done with sticky notes, OneNote, and human memory. A single missed contradiction can lose a case. There is no intelligent memory tooling for legal professionals.

**Core pain points:**
- Critical contradictions buried across hundreds of pages go undetected
- Rejected arguments and tried-and-failed strategies are forgotten and repeated
- Senior lawyers carry tribal knowledge in their heads — when they leave, it's gone
- No tool connects knowledge across sessions and documents automatically
- LLM calls are stateless by default — every session starts with amnesia

---

## 3. Build Strategy — Open Source Now, Cognee Cloud Migration Later

**The situation:** Cognee Cloud (`platform.cognee.ai`) is currently at signup capacity. Many hackathon participants, including this team, cannot create an account or obtain a `COGWIT_API_KEY`. Given a compressed 6-day build window, waiting for this to clear is not a safe plan.

**The decision:** Build the entire project now on the **open-source `cognee` pip package** — self-hosted, no signup required, fully documented, works immediately. Open-source `cognee` and Cognee Cloud's `cogwit-sdk` wrap the **same underlying memory lifecycle** (add → cognify → search → memify); Cognee Cloud is simply the hosted version of this same engine. This is not a lesser substitute — it's the same architecture, undeployed to the managed platform.

**Why the migration stays cheap:** every Cognee call in the codebase lives inside exactly one file, `memory_store.py`. No other module ever imports `cognee` or `cogwit_sdk` directly. Migrating later means rewriting one file's internals, not the project. Full technical detail and the migration checklist live in `LLD.md` Sections 0, 3.3A, and 10.

**Two possible outcomes by submission day:**
- **If Cognee Cloud signup opens in time:** migrate following the `LLD.md` checklist, re-test against `TEST_CASES.md`, and submit naming Cognee Cloud explicitly — eligible for the iPhone 17 "Best Use of Cognee Cloud" prize.
- **If it does not open in time:** submit on open-source `cognee`. This still satisfies the general "Best Use of Cognee" judging criterion and the "Best Use of Open Source" prize track. Only the iPhone 17-specific prize becomes unreachable — every other judging criterion, and the Qwen submission, is entirely unaffected. State this plainly in the README as a known platform capacity issue during the hackathon window.

---

## 4. Why Cognee + Qwen Together

| Need | Who provides it |
|---|---|
| Reasoning: extract facts, detect contradictions, judge staleness, write briefs | **Qwen2.5-72B** (Qwen Cloud) |
| Permanent, structured memory: knowledge graph + vector store | **Cognee** — `add()` (open-source now; `cogwit-sdk`'s `add()` after migration) |
| Building the knowledge graph from ingested data | **Cognee** — `cognify()` |
| Querying memory across sessions | **Cognee** — `search()` |
| Pruning stale nodes, enrichment | **Cognee** — `memify()` |
| Surgically deleting outdated case data | **Cognee** — dataset deletion/pruning |

This is not a redundant pairing — Qwen is the reasoning engine, Cognee is the memory substrate (self-hosted now, optionally hosted via Cognee Cloud later). Neither replaces the other.

---

## 5. Goals and Non-Goals

### Goals
- Persistent memory that survives across browser sessions and days, via Cognee's knowledge graph
- Automatic contradiction detection between any two ingested documents, via Qwen reasoning over Cognee's search results
- Staleness handling via Cognee's `memify()` pruning/enrichment, informed by Qwen's judgment of what's outdated
- Natural language Q&A over all case memory via Cognee `search()` + Qwen synthesis
- Trial prep brief generation within a context budget
- Deep, visible use of all four Cognee lifecycle stages (add, search, memify, dataset deletion) — required for "Best Use of Cognee" judging criterion
- **Deep, visible use of Cognee Cloud specifically** if migration completes in time — required for the iPhone 17 prize
- Deployment proof for Alibaba Cloud (Qwen requirement)

### Non-Goals
- Not a general-purpose legal research tool
- Not a document OCR or PDF parser (text paste only for v1)
- Not a court filing system or case management platform
- Not a replacement for legal advice
- Not building a custom graph database — Cognee's hybrid graph-vector store replaces this entirely
- Not blocking the build on Cognee Cloud signup access — open-source `cognee` is the primary build target; Cognee Cloud is a migration, not a prerequisite

---

## 6. System Overview

```
┌─────────────────────────────────────────────┐
│              Next.js Frontend               │
│  Ingest UI · Query UI · Contradiction View  │
│         Trial Brief · Case Manager          │
└───────────────┬─────────────────────────────┘
                │ HTTP / REST
┌───────────────▼─────────────────────────────┐
│      LangGraph Agent Orchestrator (Python)  │
│  classify_intent → ingest_node / query_node │
│  staleness_node (via memify)                │
│  brief_node                                 │
└──────┬──────────────────┬───────────────────┘
       │                  │
┌──────▼──────┐   ┌───────▼──────────────────┐
│ Qwen Cloud  │   │  Cognee (open-source)     │
│  72B Infer  │   │  add · cognify · search  │
│  Embedding  │   │  memify · dataset delete │
└─────────────┘   │  (self-hosted now ──►     │
                   │   migrates to Cognee     │
                   │   Cloud / cogwit-sdk     │
                   │   if signup access opens)│
                   └──────────┬───────────────┘
                              │
                  ┌───────────▼──────────────────┐
                  │   Alibaba Cloud (Qwen reqt.) │
                  │   ECS (backend) · OSS (docs) │
                  └──────────────────────────────┘
```

---

## 7. Architecture Components

### 7.1 Frontend — Next.js (React)

| Screen | Purpose |
|---|---|
| `/ingest` | Paste document text, select case, trigger extraction + Cognee `add()` + `cognify()` |
| `/query` | Natural language Q&A, calls Cognee `search()` then Qwen synthesis |
| `/contradictions` | Visual list of contradiction pairs with confidence scores |
| `/brief` | One-click trial prep brief generation |

### 7.2 Agent Layer — LangGraph

Stateful agent routing every request through the correct pipeline.

**Agent nodes:**
- `classify_intent` — determines if input is ingest, query, or brief
- `ingest_node` — extraction (Qwen) → Cognee `add()` + `cognify()` → contradiction detection (Qwen, using Cognee `search()` for raw candidates) → Cognee `memify()` to enrich and flag stale nodes
- `query_node` — Cognee `search()` → Qwen answer synthesis with citations
- `brief_node` — Cognee `search()` for top contradictions/assertions → Qwen brief generation

### 7.3 AI Reasoning Layer — Qwen Cloud

| Model | Purpose |
|---|---|
| `qwen2.5-72b-instruct` | Assertion extraction, contradiction detection, staleness judgment, QA reasoning, brief generation |
| `text-embedding-v3` | Used to configure open-source `cognee`'s embedding provider (not needed after migrating to Cognee Cloud, which manages this internally) |

Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (confirmed via Qwen Cloud hackathon resources — international endpoint)

### 7.4 Memory Layer — Cognee

Open-source `cognee` (current build) replaces any custom memory engine entirely. See `LLD.md` Section 0 and 3.3A for the Cognee Cloud migration variant.

| Cognee call | CourtMind usage |
|---|---|
| `cognee.add(data, dataset_name)` | Ingests extracted assertions and case metadata |
| `cognee.cognify(datasets=[...])` | Builds/updates the knowledge graph from newly added data |
| `cognee.search(query_text, dataset_name)` | Retrieval — used both for contradiction-candidate lookup and user-facing Q&A |
| `cognee.memify(datasets=[...])` | Post-ingestion enrichment and stale-node pruning |
| Dataset deletion/pruning | Archives a closed case's memory |

One **Cognee dataset per legal case** — `dataset_name` is set to the case's identifier throughout.

### 7.5 Infrastructure

| Service | Role | Required by |
|---|---|---|
| Alibaba Cloud ECS | Hosts Python backend + LangGraph runtime | Qwen hackathon |
| Alibaba Cloud OSS | Stores raw uploaded document blobs | Qwen hackathon |
| Cognee (self-hosted, current) / Cognee Cloud (if migrated) | Hosts the memory layer | Cognee hackathon |
| Qwen Cloud API | External AI inference via DashScope | Qwen hackathon |
| Vercel | Frontend hosting | Both |

---

## 8. Key User Flows

### Flow 1 — Document Ingestion
```
User pastes text → POST /api/ingest
→ LangGraph: classify_intent (ingest)
→ Qwen extracts assertions as structured JSON
→ cognee.add() stores each assertion + source metadata into a dataset (one per case)
→ cognee.cognify() builds/updates the knowledge graph for that dataset
→ cognee.search() fetches related existing assertions as contradiction candidates
→ Qwen compares new vs. existing assertions → detects contradictions
→ cognee.add() stores contradiction relationships as additional graph data
→ cognee.cognify() re-runs to incorporate the new relationships
→ cognee.memify() runs enrichment + flags stale nodes
→ UI displays extracted assertions + any contradictions found
```

### Flow 2 — Natural Language Query
```
User asks question → POST /api/query
→ LangGraph: classify_intent (query)
→ cognee.search(query_text=question, dataset_name=case_id)
→ Qwen synthesises answer from recalled facts, citing sources
→ UI displays answer + linked contradictions + staleness indicators
```

### Flow 3 — Trial Brief Generation
```
User clicks Generate Brief → POST /api/brief
→ cognee.search() — fetch top contradictions and key assertions for the case dataset
→ Qwen generates structured brief within word budget
→ UI renders: Top Contradictions · Unresolved Questions · Key Assertions
```

### Flow 4 — Case Closure (Forgetting)
```
User archives a case →
→ Cognee dataset deletion/pruning scoped to that case_id
→ Memory removed from active retrieval; archival/export handled before deletion if retention is needed
→ UI confirms case archived
```

**Note:** all four flows above run identically whether on open-source `cognee` (current build) or Cognee Cloud's `cogwit-sdk` (post-migration) — only the underlying client call inside `memory_store.py` changes; the flow shape itself does not.

---

## 9. Memory Architecture Mapping to Judging Criteria

| Judging criterion (Cognee — "The Hangover Part AI") | How CourtMind satisfies it |
|---|---|
| Best Use of Cognee Cloud (iPhone 17) | Reachable if Cognee Cloud signup opens and migration completes — built on `cogwit-sdk` against the hosted platform, using `add`, `cognify`, two distinct `search` query types, and `memify` meaningfully, with the Cognee Cloud dashboard shown as proof |
| Best Use of Cognee (general lifecycle depth) | Reachable regardless of signup status — all four lifecycle stages used purposefully on open-source `cognee`: ingest, recall, enrich/prune, archive |
| Potential Impact | Real, painful legal workflow — contradiction tracking across sessions |
| Creativity & Innovation | Contradiction-graph reasoning on top of Cognee's graph-vector store is a novel application |
| Technical Excellence | Clean separation: Cognee = memory, Qwen = reasoning, LangGraph = orchestration |
| User Experience | Four focused screens, clear staleness/contradiction visual indicators |
| Presentation Quality | README, architecture diagram, 3-minute demo video |

| Judging criterion (Qwen Track 1) | How CourtMind satisfies it |
|---|---|
| Efficient memory storage and retrieval | Cognee's hybrid graph-vector store |
| Timely forgetting of outdated information | Cognee `memify()` + dataset deletion |
| Recalling critical memories within limited context windows | Cognee `search()` returns a ranked, relevant subset; Qwen synthesises within token budget |

---

## 10. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Query response time | < 5 seconds for search + synthesis |
| Ingestion time | < 15 seconds per document (add + cognify) |
| Cross-session persistence | Indefinite (Cognee-managed graph + vector store, self-hosted or Cloud) |
| Context window budget | Cognee returns top-ranked subset; Qwen 72B context fits comfortably |
| Availability | Best-effort (hackathon scope); if migrated, subject to Cognee Cloud free-tier ($35 `COGNEE-35` credit) limits |
| AI assistant disclosure | Must declare Claude usage in Cognee submission per Rule 8 |

---

## 11. Technology Stack Summary

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | Python 3.11, FastAPI, LangGraph |
| Memory layer | **Open-source `cognee`** (current build) — migrates to **Cognee Cloud via `cogwit-sdk`** if signup access opens in time |
| AI Reasoning | Qwen2.5-72B via Qwen Cloud DashScope |
| Cloud Infra | Alibaba Cloud ECS + OSS (Qwen requirement) · Cognee Cloud managed platform (only if migrated) |
| Frontend Deploy | Vercel |
| Version Control | GitHub (MIT License, public, open source) |

---

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Cannot start coding before Jun 29 (Cognee Rule 9) | All planning, docs finalised now; Day 1 of build is pure execution |
| Cognee Cloud signup at capacity, blocking `cogwit-sdk` access | Build on open-source `cognee` now (Section 3); migrate only if/when signup opens, following `LLD.md` Section 10's checklist; submit on open-source if it never opens |
| Heavily compressed build window (4 days build + 2 days test/polish/submit, see `Roadmap.md`) | Roadmap prioritises ingest → search → contradictions → memify → agent+UI in parallel → deploy, in that strict order; contradiction detection never gets compressed further |
| Open-source `cognee`'s exact method signatures (`cognify`/`search`/`memify` parameter names) unconfirmed until hands-on | Resolve on Day 1 with a real round trip; log confirmed signatures in `BUILD_LOG.md` before building anything that depends on them |
| Two submissions, one codebase, different judging criteria | Keep README sections distinct per hackathon; emphasise Cognee lifecycle depth for Cognee judges, Qwen reasoning depth for Qwen judges |
| AI assistant non-disclosure risk (Cognee Rule 8) | Explicitly declare Claude/AI assistant usage in Cognee submission text |
| Qwen Cloud signup not listing India as a region | Resolve via Qwen Cloud Discord or Devpost-linked coupon form before Jun 29; not an actual eligibility exclusion per official rules |

---

*Document owner: CourtMind Team · Cognee submission: Jul 5, 2026 · Qwen submission: Jul 9, 2026*
