"use client";
import { useState } from "react";
import { useCase } from "../../components/CaseContext";
import { api, type IngestResponse } from "../../lib/api";
import { AssertionCard } from "../../components/AssertionCard";
import { ContradictionCard } from "../../components/ContradictionCard";

export default function IngestPage() {
  const { activeCaseId, isHydrated } = useCase();
  const [documentText, setDocumentText] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
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

  const handleIngest = async () => {
    if (!activeCaseId || !documentText || !sourceLabel) {
      setError("Please select a case, enter a source label, and paste document text.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.ingestDocument(activeCaseId, documentText, sourceLabel, speaker || undefined);
      setResult(res);
      // Clear inputs on success
      setDocumentText("");
      setSourceLabel("");
      setSpeaker("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Ingest Document</h1>
        <p className="text-slate-400 text-sm">
          Paste any legal text — depositions, statements, emails, contracts.
          CourtMind extracts every factual assertion and detects contradictions against existing case memory.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Source Label *</label>
          <input
            type="text"
            placeholder="e.g. Martinez Deposition p.1"
            value={sourceLabel}
            onChange={(e) => setSourceLabel(e.target.value)}
            disabled={loading}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 disabled:opacity-50"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Speaker (optional)</label>
          <input
            type="text"
            placeholder="e.g. John Martinez"
            value={speaker}
            onChange={(e) => setSpeaker(e.target.value)}
            disabled={loading}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 disabled:opacity-50"
          />
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-slate-300">Document Text *</label>
        <textarea
          rows={10}
          placeholder="Paste deposition, witness statement, contract, or email text here…"
          value={documentText}
          onChange={(e) => setDocumentText(e.target.value)}
          disabled={loading}
          className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono disabled:opacity-50"
        />
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleIngest}
          disabled={loading || !activeCaseId || !documentText || !sourceLabel}
          className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Ingesting into Cognee Cloud (this may take up to a minute)...
            </>
          ) : (
            "Ingest Document"
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6 mt-8">
          <div className="bg-green-950/30 border border-green-800/50 rounded-lg p-4">
            <p className="text-green-400 font-semibold flex items-center gap-2">
              <span>✓ Ingested successfully: {result.assertions_extracted} assertions extracted</span>
              {result.contradictions_found > 0 && (
                <span className="ml-2 px-2 py-0.5 rounded-full bg-red-900/50 text-red-300 text-xs border border-red-800/50">
                  ⚠️ {result.contradictions_found} contradiction{result.contradictions_found !== 1 ? "s" : ""} detected
                </span>
              )}
            </p>
          </div>

          {result.contradictions.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-red-400 flex items-center gap-2">
                <span>⚠️</span> Contradictions Found
              </h3>
              <div className="grid gap-4">
                {result.contradictions.map((c, i) => (
                  <ContradictionCard key={i} contradiction={c} index={i} />
                ))}
              </div>
            </div>
          )}

          {result.assertions.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-slate-300">Extracted Assertions</h3>
              <div className="grid gap-3">
                {result.assertions.map((a, i) => (
                  <AssertionCard key={i} assertion={a} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
