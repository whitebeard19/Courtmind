"use client";
import { useState } from "react";
import { useCase } from "../../components/CaseContext";
import { api, type QueryResponse } from "../../lib/api";
import ReactMarkdown from "react-markdown";

export default function QueryPage() {
  const { activeCaseId, isHydrated } = useCase();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
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

  const handleQuery = async () => {
    if (!activeCaseId || !question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.queryCase(activeCaseId, question);
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

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">Question</label>
        <textarea
          rows={3}
          placeholder="What did the witness say about the contract signing date?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleQuery()}
          disabled={loading}
          className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 disabled:opacity-50"
        />
        <div className="flex flex-wrap gap-2 text-xs">
          {exampleQuestions.map((q) => (
            <button
              key={q}
              onClick={() => setQuestion(q)}
              disabled={loading}
              className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-white px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleQuery}
        disabled={loading || !activeCaseId || !question.trim()}
        className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
      >
        {loading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Searching Cognee Cloud memory…
            </>
          ) : (
            "Ask Question"
          )}
      </button>

      {error && (
        <div className="bg-red-950 border border-red-800 text-red-300 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6 mt-8">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wide">Answer</h3>
            <div className="text-white leading-relaxed prose prose-invert prose-amber max-w-none">
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">
                Memory Retrieved from Cognee Cloud ({result.sources.length} chunks)
              </h3>
              <div className="grid gap-2">
                {result.sources.map((s, i) => (
                  <details
                    key={i}
                    className="bg-slate-900 border border-slate-800 rounded-lg group"
                  >
                    <summary className="p-3 text-sm text-slate-300 cursor-pointer font-medium hover:text-white flex items-center">
                      <span className="mr-2 text-slate-500 group-open:rotate-90 transition-transform">▶</span>
                      Source Chunk {i + 1}
                    </summary>
                    <div className="p-3 pt-0 text-xs text-slate-400 font-mono border-t border-slate-800 mt-2">
                      {s}
                    </div>
                  </details>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
