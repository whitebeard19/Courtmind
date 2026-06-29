"use client";
import { useState } from "react";
import { CaseSelector } from "../../components/CaseSelector";
import { api, type QueryResponse } from "../../lib/api";

export default function QueryPage() {
  const [caseId, setCaseId] = useState("");
  const [caseName, setCaseName] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async () => {
    if (!caseId || !question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.queryCase(caseId, question);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const exampleQuestions = [
    "What did Martinez say about the meeting date?",
    "Who attended the quarterly review meeting?",
    "Was the vendor contract signed?",
    "Are there any contradictions about the meeting location?",
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Query Case Memory</h1>
        <p className="text-slate-400 text-sm">
          Ask any question about your case. Cognee Cloud searches the persistent knowledge graph
          and Qwen synthesises a sourced, contradiction-aware answer.
        </p>
      </div>

      <CaseSelector
        value={caseId}
        onChange={(id, name) => { setCaseId(id); setCaseName(name); }}
      />

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">Question</label>
        <textarea
          rows={3}
          placeholder="What did the witness say about the contract signing date?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleQuery()}
          className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
        />
        <div className="flex flex-wrap gap-2 text-xs">
          {exampleQuestions.map((q) => (
            <button
              key={q}
              onClick={() => setQuestion(q)}
              className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white px-2 py-1 rounded transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleQuery}
        disabled={loading || !caseId || !question.trim()}
        className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors"
      >
        {loading ? "Searching Cognee Cloud memory…" : "Ask Question"}
      </button>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-semibold text-amber-400">Answer</h3>
            <p className="text-white leading-relaxed">{result.answer}</p>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-400">
                Memory Retrieved from Cognee Cloud ({result.sources.length} chunks)
              </h3>
              {result.sources.map((s, i) => (
                <div
                  key={i}
                  className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 font-mono"
                >
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
