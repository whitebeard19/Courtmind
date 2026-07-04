# CourtMind — API Contract (API_CONTRACT.md)

**Purpose:** This is the binding contract between backend and frontend. Whichever AI model is building either side must follow these exact shapes — no inventing fields, no renaming keys, no guessing.

**Base URL:**
- Local dev: `http://localhost:8000`
- Deployed: value of `NEXT_PUBLIC_API_URL`

All routes are prefixed `/api/`. All request and response bodies are JSON. All timestamps are ISO 8601 strings. Internally, `case_id` doubles as the Cognee Cloud `dataset_name` — this mapping never changes.

---

## `POST /api/cases`

Create a new case.

**Request:**
```json
{
  "name": "string, required",
  "description": "string, optional"
}
```

**Response (200):**
```json
{
  "case_id": "string",
  "name": "string",
  "status": "active",
  "created_at": "ISO 8601 string"
}
```

---

## `GET /api/cases`

List all cases for the case selector dropdown.

**Response (200):**
```json
{
  "cases": [
    { "case_id": "string", "name": "string", "status": "active | archived", "created_at": "ISO 8601 string" }
  ]
}
```

---

## `POST /api/ingest`

Ingest a document into a case's memory.

**Request:**
```json
{
  "case_id": "string, required",
  "document_text": "string, required",
  "source_label": "string, e.g. 'Witness A deposition - 2024-03-15', required",
  "speaker": "string, optional, name of person if known"
}
```

**Response (200):**
```json
{
  "assertions_extracted": 7,
  "contradictions_found": 2,
  "assertions": [
    { "text": "string", "speaker": "string or null", "event_date": "string or null" }
  ],
  "contradictions": [
    {
      "assertion_a": "string",
      "assertion_b": "string",
      "reason": "string",
      "confidence": 0.91
    }
  ]
}
```

**Error (400):** `{ "error": "document_text is required" }`  
**Error (500):** `{ "error": "string describing what failed internally" }`

---

## `POST /api/query`

Ask a natural language question over a case's memory.

**Request:**
```json
{
  "case_id": "string, required",
  "question": "string, required"
}
```

**Response (200):**
```json
{
  "answer": "string — full synthesised answer text",
  "sources": [ "string — raw context returned from Cognee Cloud's GRAPH_COMPLETION search" ]
}
```

**Note:** the exact shape of each entry in `sources` depends on the confirmed `search()` return type (see `BUILD_LOG.md`) — frontend should treat each item defensively (render as text, don't assume nested fields exist) until confirmed.

**Error (400):** `{ "error": "question is required" }`

---

## `POST /api/brief`

Generate a trial prep brief for a case.

**Request:**
```json
{
  "case_id": "string, required",
  "case_name": "string, required",
  "max_words": 500
}
```

**Response (200):**
```json
{
  "top_contradictions": [
    {
      "summary": "string",
      "assertion_a": "string",
      "assertion_b": "string",
      "severity": "high | medium | low",
      "recommended_action": "string"
    }
  ],
  "unresolved_questions": ["string"],
  "key_assertions": [
    { "text": "string", "source": "string", "importance": "string" }
  ],
  "brief_summary": "string"
}
```

---

## `GET /api/contradictions`

Fetch contradictions for a case, for the `/contradictions` screen.

**Request params:** `case_id` (required), `min_confidence` (optional, default 0.5)

**Response (200):**
```json
{
  "contradictions": [
    {
      "assertion_a": "string",
      "assertion_b": "string",
      "reason": "string",
      "confidence": 0.91
    }
  ]
}
```

---

## `PATCH /api/cases/:case_id/archive`

Archive a case — triggers deletion of that case's Cognee Cloud dataset.

**Response (200):**
```json
{ "case_id": "string", "status": "archived" }
```

---

## Conventions Both Sides Must Follow

- All `case_id` values are strings, and map 1:1 to a Cognee Cloud `dataset_name`. The backend additionally tracks Cognee's own `dataset_id` internally — this is never exposed to the frontend.
- Confidence and score values are always floats between 0.0 and 1.0.
- Missing/unknown optional fields are `null`, never omitted from the JSON object and never an empty string standing in for null.
- Every error response has the shape `{ "error": "string" }` — frontend should always check for this key before reading expected success fields.
- Frontend should treat staleness-related UI (badges, colors) as derived from whatever `memify()` actually exposes — confirm the real field name during build (see `BUILD_LOG.md`) and update this contract once confirmed; do not assume a `staleness_score` field exists on the wire until verified.

---

*If a backend response shape needs to change, update this file first, log the change in BUILD_LOG.md, then update both backend and frontend code to match.*
