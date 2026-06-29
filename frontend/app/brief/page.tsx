"use client";
import { useState } from "react";
import { CaseSelector } from "../../components/CaseSelector";
import { api, type BriefResponse } from "../../lib/api";

const SEVERITY_COLORS = {
  high: "text-red-400 bg-red-950 border-red-800",
  medium: "text-orange-400 bg-orange-950 border-orange-800",
  low: "text-yellow-400 bg-yellow-950 border-yellow-800",
};

export default function BriefPage() {
  const [caseId, setCaseId] = useState("");
  const [caseName, setCaseName] = useState("");
  const [loading, setLoading] = useState(false);
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!caseId || !caseName) return;
    setLoading(true);
    setError(null);
    setBrief(null);
    try {
      const res = await api.generateBrief(caseId, caseName, 500);
      setBrief(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Trial Preparation Brief</h1>
        <p className="text-slate-400 text-sm">
          Generate a structured trial brief from Cognee Cloud memory — top contradictions,
          unresolved questions, and key assertions, ranked by importance.
        </p>
      </div>

      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <CaseSelector
            value={caseId}
            onChange={(id, name) => { setCaseId(id); setCaseName(name); }}
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !caseId}
          className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-5 py-2 rounded-lg transition-colors whitespace-nowrap"
        >
          {loading ? "Generating brief…" : "Generate Brief"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {brief && (
        <div className="space-y-6">
          {/* Executive Summary */}
          <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-5">
            <h3 className="text-amber-400 font-semibold mb-2">Executive Summary</h3>
            <p className="text-white leading-relaxed">{brief.brief_summary}</p>
          </div>

          {/* Top Contradictions */}
          {brief.top_contradictions?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                ⚡ Top Contradictions
              </h3>
              {brief.top_contradictions.map((c, i) => (
                <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-white font-medium">{c.summary}</p>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border font-semibold ml-3 shrink-0 ${SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.low}`}
                    >
                      {c.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                    <div className="bg-slate-800 rounded p-2">
                      <span className="text-slate-500">A: </span>{c.assertion_a}
                    </div>
                    <div className="bg-slate-800 rounded p-2">
                      <span className="text-slate-500">B: </span>{c.assertion_b}
                    </div>
                  </div>
                  <p className="text-amber-400 text-sm">
                    → {c.recommended_action}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Unresolved Questions */}
          {brief.unresolved_questions?.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                ❓ Unresolved Questions
              </h3>
              <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
                {brief.unresolved_questions.map((q, i) => (
                  <div key={i} className="px-4 py-3 text-sm text-slate-300">
                    {i + 1}. {q}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Assertions */}
          {brief.key_assertions?.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                📌 Key Assertions
              </h3>
              {brief.key_assertions.map((a, i) => (
                <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1">
                  <p className="text-white text-sm">{a.text}</p>
                  <div className="flex gap-4 text-xs text-slate-500">
                    <span>Source: {a.source}</span>
                  </div>
                  <p className="text-slate-400 text-xs italic">{a.importance}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
