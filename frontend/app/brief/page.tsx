"use client";
import { useState } from "react";
import { useCase } from "../../components/CaseContext";
import { api, type BriefResponse } from "../../lib/api";

const SEVERITY_COLORS = {
  high: "text-red-400 bg-red-950/50 border-red-800/50",
  medium: "text-amber-400 bg-amber-950/50 border-amber-800/50",
  low: "text-yellow-400 bg-yellow-950/50 border-yellow-800/50",
};

export default function BriefPage() {
  const { activeCaseId, activeCaseName, isHydrated } = useCase();
  const [loading, setLoading] = useState(false);
  const [brief, setBrief] = useState<BriefResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isHydrated) return null;

  if (!activeCaseId) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
        <div className="text-6xl">📁</div>
        <h2 className="text-2xl font-bold text-white">No Case Selected</h2>
        <p className="text-slate-400">
          Please select or create a case from the top right menu to continue.
        </p>
      </div>
    );
  }

  const handleGenerate = async () => {
    if (!activeCaseId || !activeCaseName) return;
    setLoading(true);
    setError(null);
    setBrief(null);
    try {
      const res = await api.generateBrief(activeCaseId, activeCaseName, 500);
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

      <div className="flex items-center">
        <button
          onClick={handleGenerate}
          disabled={loading || !activeCaseId}
          className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Brief (this may take ~60 seconds)…
            </>
          ) : (
            "Generate Brief"
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {brief && (
        <div className="space-y-8 mt-8">
          {/* Executive Summary */}
          <div className="bg-amber-950/20 border border-amber-800/30 rounded-xl p-6">
            <h3 className="text-amber-400 font-semibold mb-3 uppercase tracking-wide text-sm">Executive Summary</h3>
            <p className="text-slate-200 leading-relaxed">{brief.brief_summary}</p>
          </div>

          {/* Top Contradictions */}
          {brief.top_contradictions?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span>⚡</span> Top Contradictions
              </h3>
              <div className="grid gap-4">
                {brief.top_contradictions.map((c, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-white font-medium">{c.summary}</p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-semibold ml-3 shrink-0 ${SEVERITY_COLORS[c.severity as keyof typeof SEVERITY_COLORS] || SEVERITY_COLORS.low}`}
                      >
                        {c.severity.toUpperCase()}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs text-slate-300">
                      <div className="bg-slate-950/50 border border-slate-800/50 rounded-lg p-3">
                        <span className="text-slate-500 font-semibold block mb-1">STATEMENT A</span>
                        {c.assertion_a}
                      </div>
                      <div className="bg-slate-950/50 border border-slate-800/50 rounded-lg p-3">
                        <span className="text-slate-500 font-semibold block mb-1">STATEMENT B</span>
                        {c.assertion_b}
                      </div>
                    </div>
                    <p className="text-amber-400 text-sm bg-amber-950/20 border border-amber-900/30 p-3 rounded-lg flex items-start gap-2">
                      <span className="mt-0.5">→</span>
                      <span>{c.recommended_action}</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unresolved Questions */}
          {brief.unresolved_questions?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span>❓</span> Unresolved Questions
              </h3>
              <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800/50 overflow-hidden">
                {brief.unresolved_questions.map((q, i) => (
                  <div key={i} className="px-5 py-4 text-sm text-slate-200 flex gap-3 hover:bg-slate-800/30 transition-colors">
                    <span className="text-slate-500 font-mono">{i + 1}.</span>
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Assertions */}
          {brief.key_assertions?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                <span>📌</span> Key Assertions
              </h3>
              <div className="grid gap-3">
                {brief.key_assertions.map((a, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
                    <p className="text-slate-200 text-sm leading-relaxed">{a.text}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500 pt-1">
                      <span className="flex items-center gap-1">
                        <span className="text-slate-400 font-medium">Source:</span> {a.source}
                      </span>
                      <span className="flex items-center gap-1 border-l border-slate-700 pl-4">
                        <span className="text-slate-400 font-medium">Importance:</span> 
                        <span className="italic">{a.importance}</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
