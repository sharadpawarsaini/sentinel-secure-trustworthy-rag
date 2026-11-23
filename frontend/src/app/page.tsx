"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import Link from "next/link";

// ─── Interfaces ────────────────────────────────────────────────────────────────

interface RetrievedChunk {
  chunk_id: string;
  source_filename: string;
  chunk_index: number;
  similarity_score: number;
  text: string;
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
  model?: string;
  provider?: string;
}

interface HealthResponse {
  status: string;
  llm_provider: string;
  llm_model: string;
  total_chunks: number;
  pipeline_phase: string;
}

interface DocumentItem {
  filename: string;
  chunk_count: number;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function getVerdictTheme(verdict: string) {
  switch (verdict) {
    case "TRUSTWORTHY":
      return {
        badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]",
        border: "border-emerald-500/30",
        meter: "from-emerald-500 to-teal-400",
        text: "text-emerald-400",
        label: "TRUSTWORTHY",
        icon: "✓"
      };
    case "PARTIALLY_SUPPORTED":
      return {
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]",
        border: "border-amber-500/30",
        meter: "from-amber-500 to-orange-400",
        text: "text-amber-400",
        label: "PARTIALLY SUPPORTED",
        icon: "⚠"
      };
    case "INSUFFICIENTLY_SUPPORTED":
      return {
        badge: "bg-orange-500/10 text-orange-400 border-orange-500/30 shadow-[0_0_15px_rgba(249,115,22,0.2)]",
        border: "border-orange-500/30",
        meter: "from-orange-500 to-amber-600",
        text: "text-orange-400",
        label: "INSUFFICIENT EVIDENCE",
        icon: "○"
      };
    case "CONTRADICTED":
      return {
        badge: "bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.25)]",
        border: "border-rose-500/30",
        meter: "from-rose-500 to-red-600",
        text: "text-rose-400",
        label: "CONTRADICTED BY CONTEXT",
        icon: "✕"
      };
    case "POTENTIALLY_HALLUCINATED":
      return {
        badge: "bg-fuchsia-500/10 text-fuchsia-400 border-fuchsia-500/30 shadow-[0_0_15px_rgba(217,70,239,0.25)]",
        border: "border-fuchsia-500/30",
        meter: "from-fuchsia-500 to-pink-500",
        text: "text-fuchsia-400",
        label: "POTENTIAL HALLUCINATION",
        icon: "⚡"
      };
    default:
      return {
        badge: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
        border: "border-zinc-500/30",
        meter: "from-zinc-500 to-zinc-400",
        text: "text-zinc-400",
        label: verdict || "EVALUATING",
        icon: "•"
      };
  }
}

function getSecurityBadge(action: string) {
  if (action === "BLOCK") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 border border-rose-500/40 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.25)]">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400 cyber-dot" />
        SECURITY BLOCK
      </span>
    );
  }
  if (action === "FLAG") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 border border-amber-500/40 text-amber-300">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 cyber-dot" />
        SECURITY FLAG
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 cyber-dot" />
      SECURITY PASS
    </span>
  );
}

// ─── Component ─────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(4);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"claims" | "evidence" | "telemetry">("evidence");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const responseRef = useRef<HTMLDivElement>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) setHealth(await res.json());
    } catch {}
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const data = await res.json();
        // data.unique_documents is list of filenames, data.total_chunks
        const docs = (data.unique_documents || []).map((name: string) => ({
          filename: name,
          chunk_count: data.total_chunks || 0
        }));
        setDocuments(docs);
      }
    } catch {}
  }, []);

  useEffect(() => {
    fetchHealth();
    fetchDocuments();
    const timer = setInterval(() => {
      fetchHealth();
      fetchDocuments();
    }, 12000);
    return () => clearInterval(timer);
  }, [fetchHealth, fetchDocuments]);

  const handleUploadFile = useCallback(async (file: File) => {
    setUploading(true);
    setUploadFeedback(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadFeedback({
          type: "success",
          msg: `Indexed "${file.name}" successfully (${data.chunks_created} chunks generated)`
        });
        fetchDocuments();
        fetchHealth();
      } else {
        setUploadFeedback({
          type: "error",
          msg: data.detail || "Failed to process document"
        });
      }
    } catch (err) {
      setUploadFeedback({ type: "error", msg: `Upload error: ${err}` });
    } finally {
      setUploading(false);
    }
  }, [fetchDocuments, fetchHealth]);

  const handleExecuteQuery = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), top_k: topK }),
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data);
        setTimeout(() => {
          responseRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 150);
      } else {
        setError(data.detail || "Pipeline evaluation failed");
      }
    } catch (err) {
      setError(`Network error: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [query, topK]);

  const handleDeleteDocument = useCallback(async (filename: string) => {
    try {
      await fetch(`/api/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      fetchDocuments();
      fetchHealth();
    } catch {}
  }, [fetchDocuments, fetchHealth]);

  const verdictTheme = result ? getVerdictTheme(result.is_abstained ? "ABSTAINED" : result.trust_verdict) : null;
  const trustPct = result ? Math.round((result.trust_score || 0) * 100) : 0;

  return (
    <div className="min-h-screen text-slate-100 relative cyber-grid">
      {/* Top Ambient Glow Bar */}
      <div className="fixed top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent z-50" />

      {/* Modern Navigation Header */}
      <header className="sticky top-0 z-40 bg-[#030305]/80 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.35)] border border-white/20">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-wider text-white">SENTINEL</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  PHASE 4 ACTIVE
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-medium">Trust-Aware Grounded RAG & Cybersecurity Architecture</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {health ? (
              <div className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-zinc-900/80 border border-white/[0.08] text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-400 cyber-dot" />
                <span className="text-zinc-400 font-medium">{health.llm_provider?.toUpperCase()} · {health.llm_model}</span>
                <span className="text-zinc-600">|</span>
                <span className="text-cyan-400 font-semibold">{health.total_chunks} chunks</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-900/80 border border-white/[0.08] text-xs text-amber-400">
                <span className="w-2 h-2 rounded-full bg-amber-400 cyber-dot" />
                Connecting to backend...
              </div>
            )}

            <Link
              href="/admin"
              className="group flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.1] text-xs font-semibold text-zinc-200 hover:text-white transition-all shadow-sm hover:border-cyan-500/40"
            >
              <span>Admin Console</span>
              <span className="text-zinc-500 group-hover:translate-x-0.5 group-hover:text-cyan-400 transition-all">→</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Pipeline Architecture Stage Indicator */}
        <section className="glass-panel p-3.5 border-white/[0.05]">
          <div className="flex items-center justify-between overflow-x-auto text-xs font-medium gap-2 text-zinc-400">
            {[
              { id: "1", title: "Input Sanitization", sub: "Injection Guard" },
              { id: "2", title: "Vector Retrieval", sub: "Dense MiniLM" },
              { id: "3", title: "Context Isolation", sub: "Poison Quarantine" },
              { id: "4", title: "LLM Generation", sub: "Gemini / Ollama" },
              { id: "5", title: "NLI Verification", sub: "DeBERTa Cross-Encoder" },
              { id: "6", title: "Trust Scoring", sub: "Adaptive Abstention" },
            ].map((step, idx) => (
              <div key={step.id} className="flex items-center gap-2 shrink-0">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-950/60 border border-white/[0.06]">
                  <span className="w-5 h-5 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-[10px] flex items-center justify-center font-bold">
                    0{step.id}
                  </span>
                  <div>
                    <p className="text-[11px] font-semibold text-zinc-200">{step.title}</p>
                    <p className="text-[9px] text-zinc-400">{step.sub}</p>
                  </div>
                </div>
                {idx < 5 && <span className="text-zinc-700 text-xs font-bold">→</span>}
              </div>
            ))}
          </div>
        </section>

        {/* 2-Column Responsive Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column: Knowledge Management (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Document Upload Widget */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-cyan-500/10 flex items-center justify-center text-cyan-400 border border-cyan-500/20">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <h2 className="text-xs font-bold tracking-widest text-zinc-300 uppercase">Knowledge Ingestion</h2>
                </div>
                <span className="text-[10px] text-zinc-400 font-mono">PDF, DOCX, TXT</span>
              </div>

              {/* Drag Drop Area */}
              <div
                className={`border-2 border-dashed rounded-xl p-7 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center gap-3 ${
                  dragActive 
                    ? "border-cyan-400 bg-cyan-500/10 shadow-[0_0_25px_rgba(6,182,212,0.2)]" 
                    : "border-white/[0.08] hover:border-cyan-500/40 bg-zinc-950/40 hover:bg-zinc-900/40"
                }`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                  const f = e.dataTransfer.files[0];
                  if (f) handleUploadFile(f);
                }}
              >
                {uploading ? (
                  <div className="flex flex-col items-center gap-3 py-2">
                    <div className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                    <p className="text-xs text-zinc-300 font-medium">Extracting & Vectorizing...</p>
                  </div>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-2xl bg-zinc-900/80 border border-white/[0.08] flex items-center justify-center text-zinc-400 group-hover:text-cyan-400 transition-colors shadow-inner">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="12" y1="18" x2="12" y2="12" />
                        <line x1="9" y1="15" x2="15" y2="15" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-zinc-200">Click to upload or drag & drop</p>
                      <p className="text-[11px] text-zinc-400 mt-1">Inspected for indirect poisoning & prompt injection</p>
                    </div>
                  </>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleUploadFile(f);
                  e.target.value = "";
                }}
              />

              {uploadFeedback && (
                <div className={`p-3 rounded-lg border text-xs leading-relaxed ${
                  uploadFeedback.type === "success"
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                    : "bg-rose-500/10 border-rose-500/30 text-rose-300"
                }`}>
                  {uploadFeedback.msg}
                </div>
              )}
            </div>

            {/* Indexed Repositories */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <ellipse cx="12" cy="5" rx="9" ry="3" />
                      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                    </svg>
                  </div>
                  <h2 className="text-xs font-bold tracking-widest text-zinc-300 uppercase">Indexed Documents</h2>
                </div>
                <button
                  onClick={fetchDocuments}
                  className="p-1.5 rounded-md hover:bg-white/[0.06] text-zinc-400 hover:text-white transition-colors"
                  title="Refresh corpus list"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 4 23 10 17 10" />
                    <polyline points="1 20 1 14 7 14" />
                    <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                  </svg>
                </button>
              </div>

              {documents.length === 0 ? (
                <div className="py-8 text-center text-zinc-400 text-xs">
                  No documents in vector database yet. Upload a corporate policy or research file above.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {documents.map((doc) => (
                    <div
                      key={doc.filename}
                      className="group flex items-center justify-between p-3 rounded-lg bg-zinc-950/50 border border-white/[0.05] hover:border-white/[0.12] transition-all"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="text-xs font-semibold text-zinc-200 truncate">{doc.filename}</p>
                        <p className="text-[10px] text-zinc-400 mt-0.5">SHA-256 chunked & embedded</p>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.filename)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-500/20 text-zinc-500 hover:text-rose-400 transition-all"
                        title="Delete document and vector embeddings"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6" />
                          <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Architecture Card */}
            <div className="glass-panel p-5 space-y-3">
              <h3 className="text-[11px] font-bold tracking-wider text-zinc-400 uppercase">Trust Evaluation Metrics</h3>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Retrieval Weight ($w_1$)</span>
                  <span className="font-mono text-cyan-400 font-semibold">25%</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>NLI Entailment Weight ($w_2$)</span>
                  <span className="font-mono text-emerald-400 font-semibold">55%</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Faithfulness Weight ($w_3$)</span>
                  <span className="font-mono text-indigo-400 font-semibold">20%</span>
                </div>
                <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-zinc-400">
                  <span>Abstention Threshold</span>
                  <span className="font-mono text-amber-400 font-semibold">&lt; 0.50</span>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Query & Live Verification Engine (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Query Input Console */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-purple-500/10 flex items-center justify-center text-purple-400 border border-purple-500/20">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                  </div>
                  <h2 className="text-xs font-bold tracking-widest text-zinc-300 uppercase">Sentinel Query Terminal</h2>
                </div>
                <span className="text-[10px] text-zinc-400 font-mono">Press Ctrl + Enter to Evaluate</span>
              </div>

              <div className="relative">
                <textarea
                  rows={3}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                      handleExecuteQuery();
                    }
                  }}
                  placeholder="Ask a question against your indexed knowledge base (e.g., 'Who is the CEO and when was the company founded?')..."
                  className="w-full rounded-xl bg-zinc-950/80 border border-white/[0.08] focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 p-4 text-sm text-zinc-100 placeholder-zinc-600 outline-none transition-all resize-none font-sans"
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
                <div className="flex items-center gap-3 text-xs text-zinc-400">
                  <span className="font-medium">Top-K Depth:</span>
                  <div className="flex items-center gap-1">
                    {[2, 3, 4, 6].map((k) => (
                      <button
                        key={k}
                        onClick={() => setTopK(k)}
                        className={`w-7 h-7 rounded-md font-mono text-xs font-bold transition-all ${
                          topK === k
                            ? "bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                            : "bg-zinc-900 border border-white/[0.06] text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        {k}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleExecuteQuery}
                  disabled={loading || !query.trim()}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-xs tracking-wider uppercase text-white bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 shadow-[0_0_20px_rgba(6,182,212,0.35)] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
                >
                  {loading ? (
                    <>
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                      <span>Analyze & Generate</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="glass-panel border-rose-500/40 p-5 text-sm text-rose-300 flex items-start gap-3">
                <span className="text-rose-400 font-bold text-base mt-0.5">✕</span>
                <div className="space-y-1">
                  <p className="font-semibold">Query Execution Error</p>
                  <p className="text-xs text-rose-300/80 leading-relaxed">{error}</p>
                </div>
              </div>
            )}

            {/* Verification Result Card */}
            {result && verdictTheme && (
              <div ref={responseRef} className="space-y-6 animate-fadeIn">
                
                {/* Composite Trust Score Banner */}
                <div className={`glass-panel p-6 ${verdictTheme.border} relative overflow-hidden`}>
                  <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${verdictTheme.badge}`}>
                        <span>{verdictTheme.icon}</span>
                        <span>{verdictTheme.label}</span>
                      </span>

                      {getSecurityBadge(result.security_action)}

                      {result.quarantined_chunks_count > 0 && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 border border-rose-500/30 text-rose-300">
                          ⚠ {result.quarantined_chunks_count} Poisoned Chunk Quarantined
                        </span>
                      )}
                    </div>

                    <div className="text-right">
                      <span className="text-[11px] text-zinc-400 uppercase font-semibold tracking-wider block">Trust Metric</span>
                      <span className={`text-3xl font-black font-mono tabular-nums ${verdictTheme.text}`}>
                        {trustPct}%
                      </span>
                    </div>
                  </div>

                  {/* Trust Progress Bar */}
                  <div className="h-3 w-full bg-zinc-950/80 rounded-full overflow-hidden p-0.5 border border-white/[0.06]">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${verdictTheme.meter} transition-all duration-1000 ease-out`}
                      style={{ width: `${Math.max(trustPct, 4)}%` }}
                    />
                  </div>
                </div>

                {/* Grounded Generated Answer Card */}
                <div className="glass-panel p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold tracking-widest text-zinc-400 uppercase">
                      {result.is_abstained ? "Abstention Notice" : "Grounded Model Response"}
                    </span>
                    <span className="text-[11px] font-mono text-zinc-400">
                      {result.provider?.toUpperCase()} · {result.model}
                    </span>
                  </div>

                  {result.is_abstained ? (
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm leading-relaxed space-y-1">
                      <p className="font-semibold text-amber-300 flex items-center gap-2">
                        <span>🛡 Sentinel Abstention Barrier Triggered</span>
                      </p>
                      <p className="text-xs text-amber-200/90">{result.abstention_reason}</p>
                    </div>
                  ) : (
                    <div className="p-5 rounded-xl bg-zinc-950/60 border border-white/[0.05] text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap font-sans">
                      {result.answer}
                    </div>
                  )}
                </div>

                {/* Detailed Breakdown Tabs */}
                <div className="glass-panel p-6 space-y-5">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                    <div className="flex gap-2">
                      {[
                        { id: "evidence", label: `Retrieved Evidence (${result.retrieved_chunks?.length || 0})` },
                        { id: "claims", label: `NLI Atomic Claims (${result.nli_claims?.length || 0})` },
                        { id: "telemetry", label: "Pipeline Telemetry" },
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setActiveTab(t.id as any)}
                          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            activeTab === t.id
                              ? "bg-cyan-500/15 border border-cyan-500/40 text-cyan-300 shadow-sm"
                              : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
                          }`}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tab 1: Retrieved Evidence */}
                  {activeTab === "evidence" && (
                    <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                      {result.retrieved_chunks && result.retrieved_chunks.length > 0 ? (
                        result.retrieved_chunks.map((chunk, idx) => (
                          <div key={chunk.chunk_id || idx} className="p-4 rounded-xl bg-zinc-950/60 border border-white/[0.05] space-y-2">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-semibold text-cyan-400 flex items-center gap-2">
                                <span className="text-zinc-500 font-mono">#{idx + 1}</span>
                                {chunk.source_filename}
                                <span className="text-zinc-600 font-mono text-[10px]">chunk {chunk.chunk_index}</span>
                              </span>
                              <span className="font-mono text-zinc-400 bg-white/[0.04] px-2 py-0.5 rounded text-[11px]">
                                Sim: {(chunk.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-xs text-zinc-300 leading-relaxed font-sans line-clamp-3">
                              {chunk.text}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-zinc-500 py-4 text-center">No retrieved chunks for this query.</p>
                      )}
                    </div>
                  )}

                  {/* Tab 2: NLI Atomic Claims */}
                  {activeTab === "claims" && (
                    <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                      {result.nli_claims && result.nli_claims.length > 0 ? (
                        result.nli_claims.map((claim, idx) => {
                          const isEntailed = claim.verdict === "ENTAILED";
                          const isContradiction = claim.verdict === "CONTRADICTION";
                          return (
                            <div
                              key={idx}
                              className="flex items-start gap-3 p-3.5 rounded-xl bg-zinc-950/60 border border-white/[0.05]"
                            >
                              <span
                                className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold tracking-wider shrink-0 mt-0.5 border ${
                                  isEntailed
                                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-300"
                                    : isContradiction
                                    ? "bg-rose-500/15 border-rose-500/30 text-rose-300"
                                    : "bg-zinc-500/15 border-zinc-500/30 text-zinc-400"
                                }`}
                              >
                                {claim.verdict}
                              </span>
                              <p className="text-xs text-zinc-200 leading-relaxed flex-1">
                                {claim.claim}
                              </p>
                              <span className="text-[11px] font-mono text-zinc-500 shrink-0">
                                {Math.round(claim.confidence * 100)}%
                              </span>
                            </div>
                          );
                        })
                      ) : (
                        <p className="text-xs text-zinc-500 py-4 text-center">No atomic claims were extracted.</p>
                      )}
                    </div>
                  )}

                  {/* Tab 3: Telemetry */}
                  {activeTab === "telemetry" && result.telemetry && (
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
                      {[
                        { label: "Input Scan", val: result.telemetry.input_scan_latency_ms },
                        { label: "Retrieval", val: result.telemetry.retrieval_latency_ms },
                        { label: "LLM Gen", val: result.telemetry.generation_latency_ms },
                        { label: "Trust Eval", val: result.telemetry.trust_eval_latency_ms },
                        { label: "Total E2E", val: result.telemetry.total_latency_ms, highlight: true },
                      ].map((item) => (
                        <div
                          key={item.label}
                          className={`p-3.5 rounded-xl border text-center ${
                            item.highlight
                              ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-300"
                              : "bg-zinc-950/60 border-white/[0.05] text-zinc-300"
                          }`}
                        >
                          <p className="text-[10px] text-zinc-500 uppercase font-semibold tracking-wider">{item.label}</p>
                          <p className="text-base font-extrabold font-mono mt-1">
                            {item.val !== undefined ? `${item.val.toFixed(0)} ms` : "—"}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                </div>

              </div>
            )}

          </div>

        </div>

      </main>

      {/* Cyber Footer */}
      <footer className="border-t border-white/[0.06] mt-20 py-8 text-center text-xs text-zinc-600">
        <p>SENTINEL Phase 4 · High-Assurance RAG & Trust Evaluation Engine</p>
        <p className="mt-1 font-mono text-[11px] text-zinc-700">MiniLM · ChromaDB · DeBERTa-v3 NLI · Gemini 3.1 Flash</p>
      </footer>
    </div>
  );
}
