import React from "react";
import { type Assertion } from "../lib/api";

interface AssertionCardProps {
  assertion: Assertion;
}

export function AssertionCard({ assertion }: AssertionCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
      <p className="text-white text-sm leading-relaxed">{assertion.text}</p>
      <div className="flex gap-4 text-xs text-slate-500">
        {assertion.speaker && (
          <span className="flex items-center gap-1">
            <span className="font-semibold text-slate-400">Speaker:</span> {assertion.speaker}
          </span>
        )}
        {assertion.event_date && (
          <span className="flex items-center gap-1">
            <span className="font-semibold text-slate-400">Date:</span> {assertion.event_date}
          </span>
        )}
      </div>
    </div>
  );
}
