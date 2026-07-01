import React from "react";
import { type Contradiction } from "../lib/api";

interface ContradictionCardProps {
  contradiction: Contradiction;
  index?: number;
}

const confidenceColor = (c: number) => {
  if (c >= 0.85) return "text-red-400 bg-red-950/50 border-red-800/50";
  if (c >= 0.7) return "text-amber-400 bg-amber-950/50 border-amber-800/50";
  return "text-yellow-400 bg-yellow-950/50 border-yellow-800/50";
};

const confidenceLabel = (c: number) => {
  if (c >= 0.85) return "High";
  if (c >= 0.7) return "Medium";
  return "Low";
};

export function ContradictionCard({ contradiction, index }: ContradictionCardProps) {
  const c = contradiction;
  
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-slate-400 text-sm font-semibold flex items-center gap-2">
          {index !== undefined && <span>#{index + 1}</span>}
          <span className="text-red-400">Contradiction</span>
        </span>
        <span
          className={`text-xs px-2 py-0.5 rounded-full border font-semibold ${confidenceColor(c.confidence)}`}
        >
          {confidenceLabel(c.confidence)} — {Math.round(c.confidence * 100)}%
        </span>
      </div>

      {/* Confidence bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-amber-500 to-red-500 h-full transition-all duration-500 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, c.confidence * 100))}%` }}
        />
      </div>

      <div className="space-y-3 text-sm pt-2">
        <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3">
          <span className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Statement A</span>
          <p className="text-slate-200 mt-1 leading-relaxed">{c.assertion_a}</p>
        </div>
        <div className="flex items-center justify-center -my-2 relative z-10">
          <span className="bg-slate-800 text-slate-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-slate-700">
            VS
          </span>
        </div>
        <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3">
          <span className="text-xs text-slate-500 font-semibold uppercase tracking-wide">Statement B</span>
          <p className="text-slate-200 mt-1 leading-relaxed">{c.assertion_b}</p>
        </div>
      </div>
      <p className="text-slate-400 text-sm italic border-l-2 border-slate-700 pl-3 py-1">
        {c.reason}
      </p>
    </div>
  );
}
