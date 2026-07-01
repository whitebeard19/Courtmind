/**
 * lib/api.ts — All backend API calls for CourtMind frontend.
 *
 * Uses NEXT_PUBLIC_API_URL from env (default: http://localhost:8000).
 * Every function here maps to exactly one API_CONTRACT.md endpoint.
 * Never construct fetch() calls inline in components — always use this module.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 180000); // 180s timeout

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      ...options,
    });
    
    let json;
    try {
      json = await res.json();
    } catch (e) {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status} ${res.statusText}`);
      }
      return {} as T;
    }

    if (!res.ok) {
      throw new Error(json?.error || json?.detail || `HTTP ${res.status}`);
    }
    return json as T;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out (exceeded 3 minutes). Please try again.');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── Types ──────────────────────────────────────────────────────

export interface Case {
  case_id: string;
  name: string;
  status: "active" | "archived";
  created_at: string;
}

export interface Assertion {
  text: string;
  speaker: string | null;
  event_date: string | null;
}

export interface Contradiction {
  assertion_a: string;
  assertion_b: string;
  reason: string;
  confidence: number;
}

export interface IngestResponse {
  assertions_extracted: number;
  contradictions_found: number;
  assertions: Assertion[];
  contradictions: Contradiction[];
}

export interface QueryResponse {
  answer: string;
  sources: string[];
}

export interface BriefContradiction {
  summary: string;
  assertion_a: string;
  assertion_b: string;
  severity: "high" | "medium" | "low";
  recommended_action: string;
}

export interface BriefKeyAssertion {
  text: string;
  source: string;
  importance: string;
}

export interface BriefResponse {
  top_contradictions: BriefContradiction[];
  unresolved_questions: string[];
  key_assertions: BriefKeyAssertion[];
  brief_summary: string;
}

// ── API Functions ──────────────────────────────────────────────

export const api = {
  createCase: (name: string, description?: string) =>
    apiFetch<Case>("/api/cases", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),

  listCases: () =>
    apiFetch<{ cases: Case[] }>("/api/cases"),

  ingestDocument: (
    case_id: string,
    document_text: string,
    source_label: string,
    speaker?: string
  ) =>
    apiFetch<IngestResponse>("/api/ingest", {
      method: "POST",
      body: JSON.stringify({ case_id, document_text, source_label, speaker }),
    }),

  queryCase: (case_id: string, question: string) =>
    apiFetch<QueryResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify({ case_id, question }),
    }),

  generateBrief: (case_id: string, case_name: string, max_words = 500) =>
    apiFetch<BriefResponse>("/api/brief", {
      method: "POST",
      body: JSON.stringify({ case_id, case_name, max_words }),
    }),

  getContradictions: (case_id: string, min_confidence = 0.5) =>
    apiFetch<{ contradictions: Contradiction[] }>(
      `/api/contradictions?case_id=${case_id}&min_confidence=${min_confidence}`
    ),

  archiveCase: (case_id: string) =>
    apiFetch<{ case_id: string; status: string }>(`/api/cases/${case_id}/archive`, {
      method: "PATCH",
    }),
};
