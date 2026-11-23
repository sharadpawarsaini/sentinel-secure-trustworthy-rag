"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface AdminStats {
  status: string;
  pipeline_phase: string;
  system_version: string;
  active_llm_provider: string;
  active_llm_model: string;
  embedding_model: string;
  embedding_dimension: number;
  vector_store_path: string;
  vector_store_collection: string;
  total_chunks_indexed: number;
  total_unique_documents: number;
  total_queries_logged: number;
  average_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
}

interface AdminChunk {
  chunk_id: string;
  source_filename: string;
  chunk_index: number;
  character_count: number;
  is_poisoned: boolean;
  is_quarantined: boolean;
  created_at?: string;
}

interface QueryRecord {
  id: number;
  timestamp: string;
  query: string;
  top_k: number;
  provider: string;
  model: string;
  latency_ms: number;
  chunks_count: number;
  top_similarity_score: number;
  answer: string;
  trust_score?: number;
  trust_verdict?: string;
  security_action?: string;
}

interface AuditData {
  recent_queries: QueryRecord[];
  recent_ingestions: Array<{
    filename: string;
    file_type: string;
    character_count: number;
    chunks_created: number;
    timestamp: string;
  }>;
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [chunks, setChunks] = useState<AdminChunk[]>([]);
  const [audit, setAudit] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "queries" | "chunks" | "ingestions">("overview");
  const [chunkFilter, setChunkFilter] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [sRes, cRes, aRes] = await Promise.all([
        fetch("/api/admin/stats"),
        fetch("/api/admin/chunks?limit=200"),
        fetch("/api/admin/audit?limit=50"),
      ]);
      if (sRes.ok) setStats(await sRes.json());
      if (cRes.ok) {
        const cd = await cRes.json();
        setChunks(cd.chunks || []);
      }
      if (aRes.ok) setAudit(await aRes.json());
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
    const timer = setInterval(fetchAll, 12000);
    return () => clearInterval(timer);
  }, [fetchAll]);

  const handleClearLogs = useCallback(async () => {
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    try {
      await fetch("/api/admin/clear", { method: "POST" });
      setAudit(null);
      setConfirmClear(false);
      fetchAll();
    } catch {}
  }, [confirmClear, fetchAll]);

  const filteredChunks = chunkFilter
    ? chunks.filter((c) => c.source_filename.toLowerCase().includes(chunkFilter.toLowerCase()))
    : chunks;

  const quarantinedCount = chunks.filter((c) => c.is_quarantined || c.is_poisoned).length;
  const queries = audit?.recent_queries || [];
  const blockedQueries = queries.filter((q) => q.security_action === "BLOCK").length;
  const trustworthyQueries = queries.filter((q) => q.trust_verdict === "TRUSTWORTHY").length;

  return (
    <div className="min-h-screen text-slate-100 relative cyber-grid">
      <div className="fixed top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent z-50" />

      {/* Admin Nav */}
      <header className="sticky top-0 z-40 bg-[#030305]/80 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-xs font-semibold text-zinc-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/[0.05]"
            >
              <span>← Back to Portal</span>
            </Link>
            <div className="h-4 w-[1px] bg-white/[0.1]" />
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white border border-white/20 shadow-[0_0_15px_rgba(99,102,241,0.3)]">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
              </div>
              <span className="font-extrabold text-sm tracking-wider text-white">SENTINEL AUDIT CONSOLE</span>
              <span className="text-[10px] font-mono bg-zinc-900 border border-white/[0.08] px-2 py-0.5 rounded text-indigo-400">
                v{stats?.system_version || "0.4.0"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => { setLoading(true); fetchAll(); }}
              className="px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-zinc-300 transition-all flex items-center gap-1.5"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10" />
                <polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
              </svg>
              <span>Refresh</span>
            </button>

            <button
              onClick={handleClearLogs}
              className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                confirmClear
                  ? "bg-rose-500/20 border-rose-500/50 text-rose-300"
                  : "bg-white/[0.04] hover:bg-white/[0.08] border-white/[0.08] text-zinc-400"
              }`}
            >
              {confirmClear ? "Confirm Clear" : "Clear Audit Logs"}
            </button>
            {confirmClear && (
              <button
                onClick={() => setConfirmClear(false)}
                className="text-xs text-zinc-500 hover:text-zinc-300"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Admin Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        
        {/* Navigation Tabs */}
        <div className="flex gap-2 border-b border-white/[0.08] pb-3 text-xs font-semibold">
          {[
            { id: "overview", label: "Executive Telemetry" },
            { id: "queries", label: `Query Audit Trail (${queries.length})` },
            { id: "chunks", label: `Vector Store Explorer (${chunks.length})` },
            { id: "ingestions", label: `Document Ingestions (${audit?.recent_ingestions?.length || 0})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl transition-all ${
                activeTab === tab.id
                  ? "bg-indigo-500/15 border border-indigo-500/40 text-indigo-300 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Overview */}
        {activeTab === "overview" && stats && (
          <div className="space-y-6">
            
            {/* System Info Card */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 cyber-dot" />
                  <span className="font-extrabold text-sm tracking-wider text-white uppercase">{stats.status}</span>
                  <span className="text-xs text-zinc-400">· {stats.pipeline_phase}</span>
                </div>
                <span className="text-[11px] font-mono text-zinc-400">{stats.vector_store_collection}</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs pt-2">
                {[
                  { label: "Active LLM Provider", value: stats.active_llm_provider.toUpperCase() },
                  { label: "Generation Model", value: stats.active_llm_model },
                  { label: "Dense Embedder", value: stats.embedding_model },
                  { label: "Embedding Dimensions", value: `${stats.embedding_dimension} dimensions` },
                ].map((item) => (
                  <div key={item.label} className="p-3.5 rounded-xl bg-zinc-950/60 border border-white/[0.05]">
                    <span className="text-[10px] text-zinc-400 uppercase font-semibold block">{item.label}</span>
                    <span className="text-xs font-bold text-zinc-200 mt-1 block truncate">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Metric KPI Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Indexed Chunks", val: stats.total_chunks_indexed, sub: `${stats.total_unique_documents} documents`, color: "text-cyan-400" },
                { label: "Total Queries Logged", val: stats.total_queries_logged, sub: "End-to-end verified", color: "text-indigo-400" },
                { label: "Average E2E Latency", val: `${stats.average_latency_ms.toFixed(0)} ms`, sub: `Min ${stats.min_latency_ms.toFixed(0)}ms · Max ${stats.max_latency_ms.toFixed(0)}ms`, color: "text-amber-400" },
                { label: "Quarantined Chunks", val: quarantinedCount, sub: `${chunks.length - quarantinedCount} clean vectors`, color: quarantinedCount > 0 ? "text-rose-400" : "text-emerald-400" },
              ].map((kpi) => (
                <div key={kpi.label} className="glass-panel p-5 space-y-1">
                  <p className="text-[10px] text-zinc-400 uppercase font-semibold tracking-wider">{kpi.label}</p>
                  <p className={`text-2xl font-black font-mono ${kpi.color}`}>{kpi.val}</p>
                  <p className="text-[11px] text-zinc-400">{kpi.sub}</p>
                </div>
              ))}
            </div>

            {/* Security KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-panel p-5 space-y-1">
                <p className="text-[10px] text-zinc-400 uppercase font-semibold tracking-wider">Trustworthy Queries</p>
                <p className="text-2xl font-black font-mono text-emerald-400">{trustworthyQueries}</p>
                <p className="text-[11px] text-zinc-400">Validated by DeBERTa NLI</p>
              </div>
              <div className="glass-panel p-5 space-y-1">
                <p className="text-[10px] text-zinc-400 uppercase font-semibold tracking-wider">Blocked Injection Queries</p>
                <p className="text-2xl font-black font-mono text-rose-400">{blockedQueries}</p>
                <p className="text-[11px] text-zinc-400">Neutralized at Input Barrier</p>
              </div>
              <div className="glass-panel p-5 space-y-1">
                <p className="text-[10px] text-zinc-400 uppercase font-semibold tracking-wider">Grounding Success Rate</p>
                <p className="text-2xl font-black font-mono text-teal-400">
                  {queries.length > 0 ? `${Math.round((trustworthyQueries / queries.length) * 100)}%` : "100%"}
                </p>
                <p className="text-[11px] text-zinc-400">Confidence entailed</p>
              </div>
              <div className="glass-panel p-5 space-y-1">
                <p className="text-[10px] text-zinc-400 uppercase font-semibold tracking-wider">Total Ingestions</p>
                <p className="text-2xl font-black font-mono text-purple-400">{audit?.recent_ingestions?.length || 0}</p>
                <p className="text-[11px] text-zinc-400">Corpus upload events</p>
              </div>
            </div>

          </div>
        )}

        {/* Tab 2: Queries */}
        {activeTab === "queries" && (
          <div className="glass-panel overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.08] bg-white/[0.02] text-zinc-400 uppercase text-[10px] font-semibold tracking-wider">
                    <th className="py-3 px-4">#</th>
                    <th className="py-3 px-4">Query</th>
                    <th className="py-3 px-4">Trust Score</th>
                    <th className="py-3 px-4">Verdict</th>
                    <th className="py-3 px-4">Security</th>
                    <th className="py-3 px-4">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {queries.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-zinc-400">No queries logged yet.</td>
                    </tr>
                  ) : (
                    queries.map((q) => (
                      <tr key={q.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 px-4 font-mono text-zinc-400">{q.id}</td>
                        <td className="py-3 px-4 max-w-sm">
                          <p className="font-semibold text-zinc-200 truncate">{q.query}</p>
                          <p className="text-[11px] text-zinc-400 truncate mt-0.5">{q.answer}</p>
                        </td>
                        <td className="py-3 px-4 font-mono font-bold">
                          {q.trust_score !== undefined ? (
                            <span className={q.trust_score >= 0.75 ? "text-emerald-400" : q.trust_score >= 0.5 ? "text-amber-400" : "text-rose-400"}>
                              {Math.round(q.trust_score * 100)}%
                            </span>
                          ) : (
                            <span className="text-zinc-600">—</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/[0.05] border border-white/[0.08]">
                            {q.trust_verdict || "PASS"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            q.security_action === "BLOCK"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "bg-emerald-500/10 text-emerald-300"
                          }`}>
                            {q.security_action || "PASS"}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{q.latency_ms.toFixed(0)} ms</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Chunks */}
        {activeTab === "chunks" && (
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <input
                type="text"
                placeholder="Search chunks by filename..."
                value={chunkFilter}
                onChange={(e) => setChunkFilter(e.target.value)}
                className="w-72 rounded-lg bg-zinc-950/80 border border-white/[0.08] px-3.5 py-2 text-xs text-zinc-200 outline-none focus:border-indigo-500/60"
              />
              <span className="text-xs text-zinc-400">{filteredChunks.length} chunks displayed</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.08] text-zinc-400 uppercase text-[10px] font-semibold">
                    <th className="py-3 px-4">Chunk ID</th>
                    <th className="py-3 px-4">Source File</th>
                    <th className="py-3 px-4">Index</th>
                    <th className="py-3 px-4">Chars</th>
                    <th className="py-3 px-4">Integrity Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {filteredChunks.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-zinc-400">No chunks indexed yet.</td>
                    </tr>
                  ) : (
                    filteredChunks.map((c) => (
                      <tr key={c.chunk_id} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-4 font-mono text-zinc-400">{c.chunk_id.slice(0, 16)}...</td>
                        <td className="py-3 px-4 font-semibold text-cyan-400">{c.source_filename}</td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{c.chunk_index}</td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{c.character_count}</td>
                        <td className="py-3 px-4">
                          {c.is_quarantined || c.is_poisoned ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              QUARANTINED
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">
                              VERIFIED CLEAN
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 4: Ingestions */}
        {activeTab === "ingestions" && (
          <div className="glass-panel overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.08] bg-white/[0.02] text-zinc-400 uppercase text-[10px] font-semibold tracking-wider">
                    <th className="py-3 px-4">Document File</th>
                    <th className="py-3 px-4">File Type</th>
                    <th className="py-3 px-4">Character Volume</th>
                    <th className="py-3 px-4">Generated Vectors</th>
                    <th className="py-3 px-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {!audit?.recent_ingestions?.length ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-zinc-400">No documents ingested in this session.</td>
                    </tr>
                  ) : (
                    audit.recent_ingestions.map((ing, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-4 font-semibold text-zinc-200">{ing.filename}</td>
                        <td className="py-3 px-4 font-mono text-cyan-400 uppercase">{ing.file_type}</td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{ing.character_count.toLocaleString()}</td>
                        <td className="py-3 px-4 font-mono text-indigo-400 font-bold">{ing.chunks_created}</td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{new Date(ing.timestamp).toLocaleTimeString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
