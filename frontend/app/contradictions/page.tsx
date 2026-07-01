"use client";
import { useState } from "react";
import { useCase } from "../../components/CaseContext";
import { api, type Contradiction } from "../../lib/api";
import { ContradictionCard } from "../../components/ContradictionCard";

export default function ContradictionsPage() {
  const { activeCaseId, activeCaseName, isHydrated } = useCase();
  const [loading, setLoading] = useState(false);
  const [contradictions, setContradictions] = useState<Contradiction[] | null>(null);
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

  const handleFetch = async () => {
    if (!activeCaseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getContradictions(activeCaseId, 0.5);
      setContradictions(res.contradictions);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
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

      <div className="flex items-center">
        <button
          onClick={handleFetch}
          disabled={loading || !activeCaseId}
          className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading Contradictions…
            </>
          ) : (
            "Load Contradictions"
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {contradictions !== null && (
        <div className="space-y-4 mt-8">
          {contradictions.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-4xl mb-3">✓</div>
              <p>No contradictions found in this case&apos;s memory.</p>
              <p className="text-xs mt-1">Ingest more documents to detect conflicts.</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-400 border-b border-slate-800 pb-4">
                <span className="font-semibold text-white">{contradictions.length} contradiction{contradictions.length !== 1 ? "s" : ""}</span> found in{" "}
                <span className="text-amber-400 font-medium">{activeCaseName || activeCaseId}</span>
              </p>
              <div className="grid gap-6">
                {contradictions
                  .sort((a, b) => b.confidence - a.confidence)
                  .map((c, i) => (
                    <ContradictionCard key={i} contradiction={c} index={i} />
                  ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
