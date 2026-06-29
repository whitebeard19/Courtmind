"use client";
import { useState } from "react";
import { CaseSelector } from "../../components/CaseSelector";
import { api, type IngestResponse } from "../../lib/api";

export default function IngestPage() {
  const [caseId, setCaseId] = useState("");
  const [caseName, setCaseName] = useState("");
  const [documentText, setDocumentText] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleIngest = async () => {
    if (!caseId || !documentText || !sourceLabel) {
      setError("Please select a case, enter a source label, and paste document text.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.ingestDocument(caseId, documentText, sourceLabel, speaker || undefined);
      setResult(res);
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

      <CaseSelector
        value={caseId}
        onChange={(id, name) => { setCaseId(id); setCaseName(name); }}
      />

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Source Label *</label>
          <input
            type="text"
            placeholder="e.g. Martinez Deposition p.1"
            value={sourceLabel}
            onChange={(e) => setSourceLabel(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-300">Speaker (optional)</label>
          <input
            type="text"
            placeholder="e.g. John Martinez"
            value={speaker}
            onChange={(e) => setSpeaker(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
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
          className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
        />
      </div>

      <button
        onClick={handleIngest}
        disabled={loading || !caseId || !documentText || !sourceLabel}
        className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors"
      >
        {loading ? "Ingesting into Cognee Cloud…" : "Ingest Document"}
      </button>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="bg-green-950 border border-green-800 rounded-lg p-4">
            <p className="text-green-300 font-semibold">
              ✓ Ingested: {result.assertions_extracted} assertions extracted
              {result.contradictions_found > 0 && (
                <span className="ml-3 text-red-400">
                  ⚠ {result.contradictions_found} contradiction{result.contradictions_found !== 1 ? "s" : ""} detected
                </span>
              )}
            </p>
          </div>

          {result.assertions.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Extracted Assertions</h3>
              {result.assertions.map((a, i) => (
                <div
                  key={i}
                  className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm"
                >
                  <p className="text-white">{a.text}</p>
                  <div className="flex gap-4 mt-1 text-xs text-slate-500">
                    {a.speaker && <span>Speaker: {a.speaker}</span>}
                    {a.event_date && <span>Date: {a.event_date}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.contradictions.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-red-400">Contradictions Found</h3>
              {result.contradictions.map((c, i) => (
                <div
                  key={i}
                  className="bg-red-950/50 border border-red-800 rounded-lg p-3 text-sm space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-red-400 font-semibold">Contradiction</span>
                    <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded-full">
                      {Math.round(c.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-slate-300">
                    <span className="text-slate-500">A:</span> {c.assertion_a}
                  </p>
                  <p className="text-slate-300">
                    <span className="text-slate-500">B:</span> {c.assertion_b}
                  </p>
                  <p className="text-slate-500 italic">{c.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
