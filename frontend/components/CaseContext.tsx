"use client";
import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface CaseContextType {
  activeCaseId: string;
  activeCaseName: string;
  setActiveCase: (id: string, name: string) => void;
  isHydrated: boolean;
}

const CaseContext = createContext<CaseContextType | undefined>(undefined);

export function CaseProvider({ children }: { children: ReactNode }) {
  const [activeCaseId, setActiveCaseId] = useState("");
  const [activeCaseName, setActiveCaseName] = useState("");
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const savedId = localStorage.getItem("courtmind_case_id");
    const savedName = localStorage.getItem("courtmind_case_name");
    if (savedId) {
      setActiveCaseId(savedId);
    }
    if (savedName) {
      setActiveCaseName(savedName);
    }
    setIsHydrated(true);
  }, []);

  const setActiveCase = (id: string, name: string) => {
    setActiveCaseId(id);
    setActiveCaseName(name);
    if (id) {
      localStorage.setItem("courtmind_case_id", id);
      localStorage.setItem("courtmind_case_name", name);
    } else {
      localStorage.removeItem("courtmind_case_id");
      localStorage.removeItem("courtmind_case_name");
    }
  };

  return (
    <CaseContext.Provider value={{ activeCaseId, activeCaseName, setActiveCase, isHydrated }}>
      {children}
    </CaseContext.Provider>
  );
}

export function useCase() {
  const context = useContext(CaseContext);
  if (context === undefined) {
    throw new Error("useCase must be used within a CaseProvider");
  }
  return context;
}
