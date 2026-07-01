import type { Metadata } from "next";
import "./globals.css";
import { CaseProvider } from "../components/CaseContext";
import { Navbar } from "../components/Navbar";

export const metadata: Metadata = {
  title: "CourtMind — Legal Litigation Memory",
  description: "AI-powered litigation memory assistant with persistent contradiction detection",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <CaseProvider>
          <Navbar />
          <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
        </CaseProvider>
      </body>
    </html>
  );
}
