"use client";
import Link from "next/link";
import { CaseSelector } from "./CaseSelector";
import { useCase } from "./CaseContext";

export function Navbar() {
  const { activeCaseId, setActiveCase } = useCase();

  return (
    <nav className="border-b border-slate-800 bg-slate-900 px-6 py-3 flex items-center gap-8 sticky top-0 z-50">
      <Link href="/" className="flex items-center gap-2 font-bold text-lg text-white">
        <span className="text-amber-400">⚖</span>
        <span>CourtMind</span>
      </Link>
      <div className="flex gap-6 text-sm">
        <Link
          href="/ingest"
          className="text-slate-300 hover:text-white transition-colors"
        >
          Ingest Documents
        </Link>
        <Link
          href="/query"
          className="text-slate-300 hover:text-white transition-colors"
        >
          Query Memory
        </Link>
        <Link
          href="/contradictions"
          className="text-slate-300 hover:text-white transition-colors"
        >
          Contradictions
        </Link>
        <Link
          href="/brief"
          className="text-slate-300 hover:text-white transition-colors"
        >
          Trial Brief
        </Link>
      </div>
      
      <div className="ml-auto flex items-center gap-4">
        <CaseSelector 
          value={activeCaseId} 
          onChange={(id, name) => setActiveCase(id, name)} 
        />
        <div className="text-xs text-slate-500 hidden md:block">
          Powered by Cognee Cloud + Qwen 2.5-72B
        </div>
      </div>
    </nav>
  );
}
