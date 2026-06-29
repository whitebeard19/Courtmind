"use client";
import { useState, useEffect } from "react";
import { api, type Case } from "../lib/api";

interface CaseSelectorProps {
  value: string;
  onChange: (caseId: string, caseName: string) => void;
}

export function CaseSelector({ value, onChange }: CaseSelectorProps) {
  const [cases, setCases] = useState<Case[]>([]);
  const [newCaseName, setNewCaseName] = useState("");
  const [creating, setCreating] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  const loadCases = async () => {
    try {
      const { cases: loaded } = await api.listCases();
      setCases(loaded.filter((c) => c.status === "active"));
    } catch (e) {
      console.error("Failed to load cases:", e);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleCreate = async () => {
    if (!newCaseName.trim()) return;
    setCreating(true);
    try {
      const created = await api.createCase(newCaseName.trim());
      await loadCases();
      onChange(created.case_id, created.name);
      setNewCaseName("");
      setShowCreate(false);
    } catch (e) {
      console.error("Failed to create case:", e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">
        Active Case
      </label>
      <div className="flex gap-2">
        <select
          value={value}
          onChange={(e) => {
            const selected = cases.find((c) => c.case_id === e.target.value);
            onChange(e.target.value, selected?.name || "");
          }}
          className="flex-1 bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
        >
          <option value="">— Select a case —</option>
          {cases.map((c) => (
            <option key={c.case_id} value={c.case_id}>
              {c.name} ({c.case_id})
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowCreate((v) => !v)}
          className="bg-slate-700 hover:bg-slate-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
        >
          + New
        </button>
      </div>

      {showCreate && (
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Case name (e.g. Martinez v. Acme Corp)"
            value={newCaseName}
            onChange={(e) => setNewCaseName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            className="flex-1 bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
          />
          <button
            onClick={handleCreate}
            disabled={creating || !newCaseName.trim()}
            className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
          >
            {creating ? "Creating…" : "Create"}
          </button>
        </div>
      )}
    </div>
  );
}
