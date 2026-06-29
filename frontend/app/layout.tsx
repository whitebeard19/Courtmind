import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

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
          <div className="ml-auto text-xs text-slate-500">
            Powered by Cognee Cloud + Qwen 2.5-72B
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
