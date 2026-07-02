"use client";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <div className="text-center py-16 space-y-4">
        <div className="text-6xl mb-4">⚖</div>
        <h1 className="text-4xl font-bold text-white">
          CourtMind
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          AI-powered litigation memory assistant. Never miss a contradiction.
          Never forget a witness statement. Never repeat a failed argument.
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <Link
            href="/ingest"
            className="bg-amber-500 hover:bg-amber-400 text-black font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Ingest Documents →
          </Link>
          <Link
            href="/query"
            className="border border-slate-600 hover:border-slate-400 text-slate-300 hover:text-white px-6 py-3 rounded-lg transition-colors"
          >
            Query Case Memory
          </Link>
        </div>
      </div>

      {/* How it works */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          {
            icon: "📄",
            title: "Ingest",
            desc: "Paste depositions, statements, emails. Qwen extracts every factual assertion.",
            href: "/ingest",
          },
          {
            icon: "🔍",
            title: "Detect",
            desc: "Cognee's graph-vector store surfaces contradictions across all documents automatically.",
            href: "/contradictions",
          },
          {
            icon: "💬",
            title: "Query",
            desc: "Ask natural language questions. Get sourced, contradiction-aware answers.",
            href: "/query",
          },
          {
            icon: "📋",
            title: "Brief",
            desc: "Generate trial prep briefs with top contradictions and unresolved questions.",
            href: "/brief",
          },
        ].map((item) => (
          <Link
            key={item.title}
            href={item.href}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-amber-500/50 transition-colors group"
          >
            <div className="text-3xl mb-3">{item.icon}</div>
            <h3 className="font-semibold text-white mb-2 group-hover:text-amber-400 transition-colors">
              {item.title}
            </h3>
            <p className="text-sm text-slate-400">{item.desc}</p>
          </Link>
        ))}
      </div>

      {/* Tech stack */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-sm text-slate-400">
        <p className="font-semibold text-slate-300 mb-3">Architecture</p>
        <div className="flex flex-wrap gap-3">
          {[
            "Cognee Cloud — persistent graph-vector memory",
            "Qwen Plus — reasoning, extraction, contradiction detection",
            "LangGraph — agent orchestration",
            "FastAPI — REST backend",
            "Next.js 14 — frontend",
          ].map((t) => (
            <span
              key={t}
              className="bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-xs"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
