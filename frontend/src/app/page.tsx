"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import Link from "next/link";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface RetrievedChunk {
  chunk_id: string;
  source_filename: string;
  chunk_index: number;
  similarity_score: number;
  text_snippet: string;
}

interface NliClaim {
  claim: string;
  verdict: string;
  confidence: number;
  supporting_chunk_id?: string;
}

interface TrustBreakdown {
  retrieval_confidence: number;
  context_relevance: number;
  nli_entailment_ratio: number;
  nli_contradiction_ratio: number;
  faithfulness_score: number;
  grounding_score: number;
  composite_score: number;
}

interface Telemetry {
  input_scan_latency_ms?: number;
  retrieval_latency_ms?: number;
  generation_latency_ms?: number;
  trust_eval_latency_ms?: number;
  total_latency_ms?: number;
  [key: string]: number | undefined;
}

interface QueryResponse {
  query: string;
  answer: string;
  trust_score: number;
  trust_verdict: string;
  is_abstained: boolean;
  abstention_reason?: string;
  security_action: string;
  retrieved_chunks: RetrievedChunk[];
  quarantined_chunks_count: number;
  nli_claims?: NliClaim[];
  trust_breakdown?: TrustBreakdown;
  telemetry?: Telemetry;
  model_used?: string;
  provider_used?: string;
}

interface HealthResponse {
  status: string;
  llm_provider: string;
  llm_model: string;
  chunks_indexed: number;
}

interface Document {
  filename: string;
  chunk_count: number;
  created_at?: string;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function trustColor(score: number): string {
  if (score >= 0.75) return "text-emerald-400";
  if (score >= 0.50) return "text-amber-400";
  return "text-red-400";
}

function trustBg(score: number): string {
  if (score >= 0.75) return "bg-emerald-500";
  if (score >= 0.50) return "bg-amber-500";
  return "bg-red-500";
}

function trustGlow(score: number): string {
  if (score >= 0.75) return "glow-green";
  if (score >= 0.50) return "glow-amber";
  return "glow-red";
}

function verdictBadge(verdict: string) {
  const map: Record<string, { color: string; bg: string; label: string }> = {
    TRUSTWORTHY: { color: "text-emerald-300", bg: "bg-emerald-500/20 border-emerald-500/40", label: "✓ TRUSTWORTHY" },
    PARTIALLY_SUPPORTED: { color: "text-amber-300", bg: "bg-amber-500/20 border-amber-500/40", label: "⚠ PARTIALLY SUPPORTED" },
    INSUFFICIENTLY_SUPPORTED: { color: "text-orange-300", bg: "bg-orange-500/20 border-orange-500/40", label: "○ INSUFFICIENTLY SUPPORTED" },
    CONTRADICTED: { color: "text-red-300", bg: "bg-red-500/20 border-red-500/40", label: "✕ CONTRADICTED" },
    POTENTIALLY_HALLUCINATED: { color: "text-pink-300", bg: "bg-pink-500/20 border-pink-500/40", label: "⚡ POTENTIALLY HALLUCINATED" },
    ABSTAINED: { color: "text-zinc-300", bg: "bg-zinc-500/20 border-zinc-500/40", label: "— ABSTAINED" },
  };
  const v = map[verdict] ?? { color: "text-zinc-300", bg: "bg-zinc-800 border-zinc-700", label: verdict };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border tracking-wider ${v.color} ${v.bg}`}>
      {v.label}
    </span>
  );
}

function securityBadge(action: string) {
  const map: Record<string, { color: string; bg: string }> = {
    PASS: { color: "text-emerald-300", bg: "bg-emerald-500/15 border-emerald-500/35" },
    FLAG: { color: "text-amber-300", bg: "bg-amber-500/15 border-amber-500/35" },
    BLOCK: { color: "text-red-300", bg: "bg-red-500/15 border-red-500/35" },
  };
  const s = map[action] ?? { color: "text-zinc-300", bg: "bg-zinc-800 border-zinc-600" };
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border tracking-wider ${s.color} ${s.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${action === "PASS" ? "bg-emerald-400" : action === "FLAG" ? "bg-amber-400" : "bg-red-400"} pulse-dot`} />
      {action}
    </span>
  );
}

function nliVerdictColor(verdict: string): string {
  if (verdict === "ENTAILED") return "text-emerald-400";
  if (verdict === "CONTRADICTION") return "text-red-400";
  return "text-zinc-400";
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function TrustMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between items-center">
        <span className="text-xs text-zinc-400 font-medium uppercase tracking-widest">Trust Score</span>
        <span className={`text-2xl font-black tabular-nums ${trustColor(score)}`}>{pct}%</span>
      </div>
      <div className="h-2.5 w-full bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${trustBg(score)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function BreakdownBar({ label, value, color = "bg-sky-500" }: { label: string; value: number; color?: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-zinc-500 w-36 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="text-xs tabular-nums text-zinc-400 w-10 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}

function LatencyBadge({ label, ms }: { label: string; ms?: number }) {
  if (ms === undefined) return null;
  return (
    <div className="flex flex-col items-center gap-1 px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg">
      <span className="text-xs text-zinc-500">{label}</span>
      <span className="text-sm font-bold text-sky-400 tabular-nums">{ms.toFixed(0)}ms</span>
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(4);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch("/api/health");
      if (r.ok) setHealth(await r.json());
    } catch {}
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const r = await fetch("/api/documents");
      if (r.ok) {
        const d = await r.json();
        setDocuments(d.documents ?? []);
      }
    } catch {}
  }, []);

  useEffect(() => {
    fetchHealth();
    fetchDocuments();
    const id = setInterval(() => { fetchHealth(); fetchDocuments(); }, 10000);
    return () => clearInterval(id);
  }, [fetchHealth, fetchDocuments]);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setUploadMsg(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await fetch("/api/documents/upload", { method: "POST", body: form });
      const j = await r.json();
      if (r.ok) {
        setUploadMsg({ type: "ok", text: `✓ Indexed "${file.name}" — ${j.chunks_created ?? "?"} chunks` });
        fetchDocuments();
        fetchHealth();
      } else {
        setUploadMsg({ type: "err", text: j.detail ?? "Upload failed" });
      }
    } catch (e) {
      setUploadMsg({ type: "err", text: `Network error: ${e}` });
    } finally {
      setUploading(false);
    }
  }, [fetchDocuments, fetchHealth]);

  const handleAsk = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch("/api/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: topK }),
      });
      const j = await r.json();
      if (r.ok) {
        setResult(j);
        setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
      } else {
        setError(j.detail ?? "Query failed");
      }
    } catch (e) {
      setError(`Network error: ${e}`);
    } finally {
      setLoading(false);
    }
  }, [query, topK]);

  const handleDeleteDoc = useCallback(async (filename: string) => {
    try {
      await fetch(`/api/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      fetchDocuments();
      fetchHealth();
    } catch {}
  }, [fetchDocuments, fetchHealth]);

  return (
    <div className="min-h-screen bg-black relative overflow-x-hidden">
      {/* Background radial gradient */}
      <div className="fixed inset-0 pointer-events-none" style={{
        background: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(56,189,248,0.07) 0%, transparent 70%), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(129,140,248,0.05) 0%, transparent 70%)"
      }} />

      {/* Top Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-900 bg-black/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Shield icon */}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <span className="font-black text-white tracking-wide text-sm">SENTINEL</span>
              <span className="ml-2 text-xs text-zinc-500 font-medium">Secure & Trustworthy RAG · Phase 4</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {health ? (
              <>
                <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
                  Connected
                </span>
                <span className="hidden sm:block text-xs text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-1 rounded-md">
                  {health.llm_provider?.toUpperCase()} · {health.llm_model}
                </span>
                <span className="text-xs text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-1 rounded-md">
                  {health.chunks_indexed} chunks
                </span>
              </>
            ) : (
              <span className="flex items-center gap-1.5 text-xs text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                Connecting…
              </span>
            )}
            <Link href="/admin" className="text-xs font-semibold text-sky-400 border border-sky-500/30 px-3 py-1 rounded-md hover:bg-sky-500/10 transition-colors">
              Admin →
            </Link>
          </div>
        </div>
      </nav>

      {/* Phase indicator banner */}
      <div className="border-b border-zinc-900 bg-zinc-950/50">
        <div className="max-w-7xl mx-auto px-4 py-2 text-xs text-zinc-500 font-mono">
          <span className="text-zinc-600">Pipeline: </span>
          {["User Input", "Input Security", "Retrieval", "Context Security", "LLM Generation", "NLI Trust Eval", "Mitigation", "Final Response"].map((step, i, arr) => (
            <span key={step}>
              <span className="text-zinc-400">{step}</span>
              {i < arr.length - 1 && <span className="text-zinc-700 mx-1">→</span>}
            </span>
          ))}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Column: Upload + Docs */}
          <div className="lg:col-span-2 space-y-4">
            {/* Upload card */}
            <div className="sentinel-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <h2 className="text-sm font-bold text-white uppercase tracking-widest">Ingest Document</h2>
              </div>

              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${dragOver ? "border-sky-400 bg-sky-500/10" : "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/30"}`}
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  const f = e.dataTransfer.files[0];
                  if (f) handleUpload(f);
                }}
              >
                {uploading ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 rounded-full border-2 border-sky-400 border-t-transparent animate-spin" />
                    <span className="text-sm text-zinc-400">Indexing…</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm text-zinc-300 font-medium">Drop file or click to browse</p>
                      <p className="text-xs text-zinc-600 mt-1">PDF · DOCX · TXT</p>
                    </div>
                  </div>
                )}
              </div>
              <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); e.target.value = ""; }} />

              {uploadMsg && (
                <div className={`mt-3 text-xs px-3 py-2 rounded-lg border ${uploadMsg.type === "ok" ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30" : "text-red-300 bg-red-500/10 border-red-500/30"}`}>
                  {uploadMsg.text}
                </div>
              )}
            </div>

            {/* Indexed documents */}
            <div className="sentinel-card p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-400">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <h2 className="text-sm font-bold text-white uppercase tracking-widest">Indexed Documents</h2>
                </div>
                <button onClick={fetchDocuments} className="text-zinc-500 hover:text-zinc-300 transition-colors">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
                    <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                  </svg>
                </button>
              </div>
              {documents.length === 0 ? (
                <p className="text-xs text-zinc-600 text-center py-4">No documents indexed yet</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {documents.map((doc) => (
                    <div key={doc.filename} className="flex items-center justify-between gap-2 px-3 py-2 bg-zinc-900/80 border border-zinc-800 rounded-lg group">
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-zinc-300 truncate">{doc.filename}</p>
                        <p className="text-xs text-zinc-600">{doc.chunk_count} chunks</p>
                      </div>
                      <button onClick={() => handleDeleteDoc(doc.filename)} className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                          <path d="M10 11v6M14 11v6M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Security + Trust legend */}
            <div className="sentinel-card p-5 space-y-3">
              <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Score Legend</h3>
              <div className="space-y-2">
                {[
                  { color: "bg-emerald-500", label: "TRUSTWORTHY", range: "≥ 75%" },
                  { color: "bg-amber-500", label: "PARTIAL / UNSUPPORTED", range: "50–74%" },
                  { color: "bg-red-500", label: "CONTRADICTED / HALLUCINATED", range: "< 50%" },
                ].map(({ color, label, range }) => (
                  <div key={label} className="flex items-center gap-2 text-xs">
                    <div className={`w-2 h-2 rounded-full ${color}`} />
                    <span className="text-zinc-400 flex-1">{label}</span>
                    <span className="text-zinc-600 font-mono">{range}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Query + Results */}
          <div className="lg:col-span-3 space-y-4">
            {/* Query card */}
            <div className="sentinel-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400">
                  <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <h2 className="text-sm font-bold text-white uppercase tracking-widest">Ask a Question</h2>
              </div>
              <textarea
                rows={3}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleAsk(); }}
                placeholder="e.g. What is the company's refund policy? (Ctrl+Enter to send)"
                className="w-full bg-zinc-900/80 border border-zinc-700 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-sky-500/70 focus:ring-1 focus:ring-sky-500/30 resize-none transition-all"
              />
              <div className="flex items-center justify-between mt-3 gap-3 flex-wrap">
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <span>Top-K</span>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="bg-zinc-900 border border-zinc-700 rounded-lg px-2 py-1 text-zinc-300 text-xs focus:outline-none focus:border-sky-500/50"
                  >
                    {[2, 3, 4, 5, 6, 8].map((k) => <option key={k} value={k}>{k}</option>)}
                  </select>
                </div>
                <button
                  onClick={handleAsk}
                  disabled={loading || !query.trim()}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-sky-500 to-indigo-600 text-white shadow-lg shadow-sky-500/20 hover:shadow-sky-500/40 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      Ask SENTINEL
                    </>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="sentinel-card border-red-500/40 p-4 text-sm text-red-300 flex items-start gap-3">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0 text-red-400">
                  <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div ref={resultRef} className="space-y-4">
                {/* Trust + Security header */}
                <div className={`sentinel-card p-5 ${trustGlow(result.trust_score)}`}>
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex flex-wrap items-center gap-2">
                      {verdictBadge(result.is_abstained ? "ABSTAINED" : result.trust_verdict)}
                      {securityBadge(result.security_action)}
                      {result.quarantined_chunks_count > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-red-500/15 border border-red-500/35 text-red-300">
                          ⚠ {result.quarantined_chunks_count} chunk{result.quarantined_chunks_count > 1 ? "s" : ""} quarantined
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-zinc-600">
                      {result.provider_used?.toUpperCase()} · {result.model_used}
                    </div>
                  </div>
                  <TrustMeter score={result.trust_score} />
                </div>

                {/* Answer */}
                <div className="sentinel-card p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400">
                      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                    </svg>
                    <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Answer</h3>
                  </div>
                  {result.is_abstained ? (
                    <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-4 text-sm text-zinc-400 italic">
                      <span className="text-zinc-500 font-semibold block mb-1">System abstained from answering.</span>
                      {result.abstention_reason}
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
                  )}
                </div>

                {/* Trust breakdown */}
                {result.trust_breakdown && (
                  <div className="sentinel-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-sky-400">
                        <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
                        <line x1="6" y1="20" x2="6" y2="14" />
                      </svg>
                      <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Trust Breakdown</h3>
                    </div>
                    <div className="space-y-2.5">
                      <BreakdownBar label="Retrieval Confidence" value={result.trust_breakdown.retrieval_confidence} color="bg-sky-500" />
                      <BreakdownBar label="Context Relevance" value={result.trust_breakdown.context_relevance} color="bg-indigo-500" />
                      <BreakdownBar label="NLI Entailment" value={result.trust_breakdown.nli_entailment_ratio} color="bg-emerald-500" />
                      <BreakdownBar label="Faithfulness" value={result.trust_breakdown.faithfulness_score} color="bg-purple-500" />
                      <BreakdownBar label="Grounding" value={result.trust_breakdown.grounding_score} color="bg-teal-500" />
                      {result.trust_breakdown.nli_contradiction_ratio > 0 && (
                        <BreakdownBar label="Contradiction ⚠" value={result.trust_breakdown.nli_contradiction_ratio} color="bg-red-500" />
                      )}
                    </div>
                  </div>
                )}

                {/* NLI Claims */}
                {result.nli_claims && result.nli_claims.length > 0 && (
                  <div className="sentinel-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-400">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                      </svg>
                      <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">NLI Claim Analysis</h3>
                      <span className="ml-auto text-xs text-zinc-600">{result.nli_claims.length} claims extracted</span>
                    </div>
                    <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                      {result.nli_claims.map((claim, i) => (
                        <div key={i} className="flex items-start gap-3 px-3 py-2.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
                          <span className={`text-xs font-bold mt-0.5 shrink-0 w-16 ${nliVerdictColor(claim.verdict)}`}>{claim.verdict}</span>
                          <p className="text-xs text-zinc-400 leading-relaxed flex-1">{claim.claim}</p>
                          <span className="text-xs text-zinc-600 tabular-nums shrink-0">{Math.round(claim.confidence * 100)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Retrieved chunks */}
                {result.retrieved_chunks && result.retrieved_chunks.length > 0 && (
                  <div className="sentinel-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-teal-400">
                        <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                      </svg>
                      <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Retrieved Context</h3>
                      <span className="ml-auto text-xs text-zinc-600">{result.retrieved_chunks.length} chunks</span>
                    </div>
                    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                      {result.retrieved_chunks.map((chunk, i) => (
                        <div key={chunk.chunk_id} className="px-3 py-2.5 bg-zinc-900/80 border border-zinc-800 rounded-lg">
                          <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-zinc-600">#{i + 1}</span>
                              <span className="text-xs text-sky-400 font-medium">{chunk.source_filename}</span>
                              <span className="text-xs text-zinc-600">chunk {chunk.chunk_index}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <div className="h-1.5 w-16 bg-zinc-800 rounded-full overflow-hidden">
                                <div className="h-full bg-sky-500/70 rounded-full" style={{ width: `${Math.round(chunk.similarity_score * 100)}%` }} />
                              </div>
                              <span className="text-xs text-zinc-500 tabular-nums">{(chunk.similarity_score * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                          <p className="text-xs text-zinc-500 leading-relaxed line-clamp-2">{chunk.text_snippet}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Latency telemetry */}
                {result.telemetry && (
                  <div className="sentinel-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400">
                        <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                      </svg>
                      <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Pipeline Latency</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <LatencyBadge label="Input Scan" ms={result.telemetry.input_scan_latency_ms} />
                      <LatencyBadge label="Retrieval" ms={result.telemetry.retrieval_latency_ms} />
                      <LatencyBadge label="Generation" ms={result.telemetry.generation_latency_ms} />
                      <LatencyBadge label="Trust Eval" ms={result.telemetry.trust_eval_latency_ms} />
                      <div className="flex flex-col items-center gap-1 px-3 py-2 bg-sky-500/10 border border-sky-500/30 rounded-lg">
                        <span className="text-xs text-sky-500">Total</span>
                        <span className="text-sm font-black text-sky-400 tabular-nums">{result.telemetry.total_latency_ms?.toFixed(0)}ms</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-900 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-4">
          <p className="text-xs text-zinc-700">
            SENTINEL Phase 4 · Built by Bhumika · Adhya · Anwesha · Sharad
          </p>
          <p className="text-xs text-zinc-700 font-mono">
            FastAPI + ChromaDB + MiniLM + DeBERTa NLI + Gemini
          </p>
        </div>
      </footer>
    </div>
  );
}
