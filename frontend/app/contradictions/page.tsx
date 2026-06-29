"use client";
import { useState } from "react";
import { CaseSelector } from "../../components/CaseSelector";
import { api, type Contradiction } from "../../lib/api";

export default function ContradictionsPage() {
  const [caseId, setCaseId] = useState("");
  const [caseName, setCaseName] = useState("");
  const [loading, setLoading] = useState(false);
  const [contradictions, setContradictions] = useState<Contradiction[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getContradictions(caseId, 0.5);
      setContradictions(res.contradictions);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const confidenceColor = (c: number) => {
    if (c >= 0.9) return "text-red-400 bg-red-950 border-red-800";
    if (c >= 0.7) return "text-orange-400 bg-orange-950 border-orange-800";
    return "text-yellow-400 bg-yellow-950 border-yellow-800";
  };

  const confidenceLabel = (c: number) => {
    if (c >= 0.9) return "High";
    if (c >= 0.7) return "Medium";
    return "Low";
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Contradiction Map</h1>
        <p className="text-slate-400 text-sm">
          Contradictions detected across all ingested documents, stored in Cognee Cloud's knowledge graph.
          Ranked by confidence score.
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
          onClick={handleFetch}
          disabled={loading || !caseId}
          className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-5 py-2 rounded-lg transition-colors whitespace-nowrap"
        >
          {loading ? "Loading…" : "Load Contradictions"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {contradictions !== null && (
        <div className="space-y-3">
          {contradictions.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-3">✓</div>
              <p>No contradictions found in this case&apos;s memory.</p>
              <p className="text-xs mt-1">Ingest more documents to detect conflicts.</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-400">
                {contradictions.length} contradiction{contradictions.length !== 1 ? "s" : ""} found in{" "}
                <span className="text-white">{caseName || caseId}</span>
              </p>
              {contradictions
                .sort((a, b) => b.confidence - a.confidence)
                .map((c, i) => (
                  <div
                    key={i}
                    className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm font-semibold">
                        Contradiction #{i + 1}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${confidenceColor(c.confidence)}`}
                      >
                        {confidenceLabel(c.confidence)} — {Math.round(c.confidence * 100)}%
                      </span>
                    </div>

                    {/* Confidence bar */}
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-amber-500 to-red-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${c.confidence * 100}%` }}
                      />
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="bg-slate-800 rounded-lg p-3">
                        <span className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Statement A</span>
                        <p className="text-white mt-1">{c.assertion_a}</p>
                      </div>
                      <div className="flex items-center gap-2 text-slate-600 text-xs font-bold justify-center">
                        ⚡ CONTRADICTS ⚡
                      </div>
                      <div className="bg-slate-800 rounded-lg p-3">
                        <span className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Statement B</span>
                        <p className="text-white mt-1">{c.assertion_b}</p>
                      </div>
                    </div>
                    <p className="text-slate-400 text-sm italic">{c.reason}</p>
                  </div>
                ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}
