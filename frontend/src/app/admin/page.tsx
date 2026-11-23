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
  retrieved_chunks_preview?: Array<{
    chunk_id: string;
    source_filename: string;
    similarity_score: number;
    text_snippet: string;
  }>;
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

// ─── Helpers ───────────────────────────────────────────────────────────────────

function trustColor(score?: number) {
  if (!score) return "text-zinc-500";
  if (score >= 0.75) return "text-emerald-400";
  if (score >= 0.50) return "text-amber-400";
  return "text-red-400";
}

function verdictPill(verdict?: string, isAbstained?: boolean) {
  if (!verdict) return <span className="text-zinc-600 text-xs">—</span>;
  const v = isAbstained ? "ABSTAINED" : verdict;
  const colors: Record<string, string> = {
    TRUSTWORTHY: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    PARTIALLY_SUPPORTED: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    CONTRADICTED: "bg-red-500/15 text-red-300 border-red-500/30",
    POTENTIALLY_HALLUCINATED: "bg-pink-500/15 text-pink-300 border-pink-500/30",
    ABSTAINED: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
    INSUFFICIENTLY_SUPPORTED: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold border ${colors[v] ?? "bg-zinc-800 text-zinc-400 border-zinc-700"}`}>
      {v.replace(/_/g, " ")}
    </span>
  );
}

function secPill(action?: string) {
  if (!action) return <span className="text-zinc-600 text-xs">—</span>;
  const colors: Record<string, string> = {
    PASS: "bg-emerald-500/15 text-emerald-300",
    FLAG: "bg-amber-500/15 text-amber-300",
    BLOCK: "bg-red-500/15 text-red-300",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${colors[action] ?? "bg-zinc-800 text-zinc-400"}`}>
      {action}
    </span>
  );
}

function KpiCard({ label, value, sub, accent = "text-sky-400" }: { label: string; value: string | number; sub?: string; accent?: string }) {
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors">
      <p className="text-xs text-zinc-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`text-2xl font-black tabular-nums ${accent}`}>{value}</p>
      {sub && <p className="text-xs text-zinc-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function TimeAgo({ ts }: { ts: string }) {
  try {
    const diff = Date.now() - new Date(ts).getTime();
    const s = Math.round(diff / 1000);
    if (s < 60) return <span>{s}s ago</span>;
    const m = Math.round(s / 60);
    if (m < 60) return <span>{m}m ago</span>;
    return <span>{Math.round(m / 60)}h ago</span>;
  } catch {
    return <span>—</span>;
  }
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [chunks, setChunks] = useState<AdminChunk[]>([]);
  const [audit, setAudit] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "chunks" | "queries" | "ingestions">("overview");
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
        setChunks(cd.chunks ?? []);
      }
      if (aRes.ok) setAudit(await aRes.json());
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 15000);
    return () => clearInterval(id);
  }, [fetchAll]);

  const handleClearLogs = useCallback(async () => {
    if (!confirmClear) { setConfirmClear(true); return; }
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
  const cleanCount = chunks.length - quarantinedCount;

  const queries = audit?.recent_queries ?? [];
  const blockedQueries = queries.filter((q) => q.security_action === "BLOCK").length;
  const trustworthyQueries = queries.filter((q) => q.trust_verdict === "TRUSTWORTHY").length;

  const tabs = [
    { id: "overview" as const, label: "Overview" },
    { id: "queries" as const, label: `Query Audit (${queries.length})` },
    { id: "chunks" as const, label: `Chunks (${chunks.length})` },
    { id: "ingestions" as const, label: `Ingestions (${audit?.recent_ingestions?.length ?? 0})` },
  ];

  return (
    <div className="min-h-screen bg-black relative">
      <div className="fixed inset-0 pointer-events-none" style={{
        background: "radial-gradient(ellipse 60% 40% at 20% 0%, rgba(129,140,248,0.06) 0%, transparent 70%)"
      }} />

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-900 bg-black/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-zinc-500 hover:text-zinc-200 transition-colors text-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              Back
            </Link>
            <div className="w-px h-5 bg-zinc-800" />
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
                </svg>
              </div>
              <span className="font-black text-white text-sm">SENTINEL Admin</span>
              {stats && (
                <span className="text-xs text-zinc-500 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-md">v{stats.system_version}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { setLoading(true); fetchAll(); }} className="text-xs text-zinc-500 hover:text-zinc-300 border border-zinc-800 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
              </svg>
              Refresh
            </button>
            <button
              onClick={handleClearLogs}
              className={`text-xs border px-3 py-1.5 rounded-lg transition-colors ${confirmClear ? "text-red-300 border-red-500/50 bg-red-500/10" : "text-zinc-500 border-zinc-800 hover:border-zinc-600"}`}
            >
              {confirmClear ? "Confirm Clear" : "Clear Logs"}
            </button>
            {confirmClear && (
              <button onClick={() => setConfirmClear(false)} className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors">
                Cancel
              </button>
            )}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading && !stats ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
            <p className="text-zinc-500 text-sm">Loading telemetry…</p>
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div className="flex gap-1 mb-6 border-b border-zinc-900 pb-0">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors -mb-px ${
                    activeTab === tab.id
                      ? "text-white border border-zinc-800 border-b-black bg-zinc-900"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Overview Tab */}
            {activeTab === "overview" && stats && (
              <div className="space-y-6">
                {/* System info */}
                <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    <span className="flex items-center gap-1.5 text-sm font-bold text-white">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
                      {stats.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-zinc-500 bg-zinc-800 border border-zinc-700 px-2 py-0.5 rounded-md">{stats.pipeline_phase}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    {[
                      { label: "LLM Provider", value: stats.active_llm_provider.toUpperCase() },
                      { label: "LLM Model", value: stats.active_llm_model },
                      { label: "Embedding Model", value: stats.embedding_model.split("/").pop() ?? stats.embedding_model },
                      { label: "Embedding Dim", value: `${stats.embedding_dimension}d` },
                      { label: "Vector Collection", value: stats.vector_store_collection },
                      { label: "Vector Store Path", value: stats.vector_store_path.split("\\").pop() ?? stats.vector_store_path },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex flex-col gap-0.5">
                        <span className="text-zinc-600">{label}</span>
                        <span className="text-zinc-300 font-medium truncate">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* KPI grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <KpiCard label="Chunks Indexed" value={stats.total_chunks_indexed} sub={`${stats.total_unique_documents} docs`} accent="text-sky-400" />
                  <KpiCard label="Queries Logged" value={stats.total_queries_logged} accent="text-indigo-400" />
                  <KpiCard label="Avg Latency" value={`${stats.average_latency_ms}ms`} sub={`min ${stats.min_latency_ms}ms · max ${stats.max_latency_ms}ms`} accent="text-amber-400" />
                  <KpiCard label="Quarantined" value={quarantinedCount} sub={`${cleanCount} clean`} accent={quarantinedCount > 0 ? "text-red-400" : "text-emerald-400"} />
                </div>

                {/* Security + Trust KPIs */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <KpiCard label="TRUSTWORTHY" value={trustworthyQueries} sub={`of ${queries.length} queries`} accent="text-emerald-400" />
                  <KpiCard label="BLOCKED Queries" value={blockedQueries} accent="text-red-400" />
                  <KpiCard label="Total Ingestions" value={audit?.recent_ingestions?.length ?? 0} accent="text-teal-400" />
                  <KpiCard
                    label="Trustworthy Rate"
                    value={queries.length > 0 ? `${Math.round((trustworthyQueries / queries.length) * 100)}%` : "—"}
                    accent="text-purple-400"
                  />
                </div>

                {/* Trust distribution mini-chart */}
                {queries.length > 0 && (() => {
                  const verdictCounts: Record<string, number> = {};
                  queries.forEach((q) => {
                    const v = q.trust_verdict ?? "UNKNOWN";
                    verdictCounts[v] = (verdictCounts[v] ?? 0) + 1;
                  });
                  const colors: Record<string, string> = {
                    TRUSTWORTHY: "bg-emerald-500",
                    PARTIALLY_SUPPORTED: "bg-amber-500",
                    INSUFFICIENTLY_SUPPORTED: "bg-orange-500",
                    CONTRADICTED: "bg-red-600",
                    POTENTIALLY_HALLUCINATED: "bg-pink-500",
                    ABSTAINED: "bg-zinc-500",
                    UNKNOWN: "bg-zinc-700",
                  };
                  return (
                    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
                      <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Trust Verdict Distribution</h3>
                      <div className="flex h-6 rounded-full overflow-hidden gap-0.5">
                        {Object.entries(verdictCounts).map(([v, count]) => (
                          <div
                            key={v}
                            title={`${v}: ${count}`}
                            className={`${colors[v] ?? "bg-zinc-700"} transition-all`}
                            style={{ width: `${(count / queries.length) * 100}%`, minWidth: "2px" }}
                          />
                        ))}
                      </div>
                      <div className="flex flex-wrap gap-3 mt-3">
                        {Object.entries(verdictCounts).map(([v, count]) => (
                          <div key={v} className="flex items-center gap-1.5 text-xs">
                            <div className={`w-2 h-2 rounded-sm ${colors[v] ?? "bg-zinc-700"}`} />
                            <span className="text-zinc-500">{v.replace(/_/g, " ")}</span>
                            <span className="text-zinc-400 font-bold">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Query Audit Tab */}
            {activeTab === "queries" && (
              <div className="space-y-3">
                {queries.length === 0 ? (
                  <div className="text-center py-16 text-zinc-600 text-sm">No queries logged yet. Ask a question from the main portal.</div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-zinc-800">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-zinc-800 bg-zinc-900/80">
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider w-8">#</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Query</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Trust</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Verdict</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Security</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Latency</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">When</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900">
                        {queries.map((q) => (
                          <tr key={q.id} className="hover:bg-zinc-900/40 transition-colors group">
                            <td className="px-4 py-3 text-zinc-700 font-mono">{q.id}</td>
                            <td className="px-4 py-3 max-w-xs">
                              <p className="text-zinc-300 truncate" title={q.query}>{q.query}</p>
                              <p className="text-zinc-600 truncate mt-0.5">{q.answer?.slice(0, 60)}…</p>
                            </td>
                            <td className="px-4 py-3">
                              {q.trust_score !== undefined ? (
                                <span className={`font-bold tabular-nums ${trustColor(q.trust_score)}`}>
                                  {Math.round(q.trust_score * 100)}%
                                </span>
                              ) : (
                                <span className="text-zinc-600">—</span>
                              )}
                            </td>
                            <td className="px-4 py-3">{verdictPill(q.trust_verdict)}</td>
                            <td className="px-4 py-3">{secPill(q.security_action)}</td>
                            <td className="px-4 py-3 tabular-nums text-zinc-500">{q.latency_ms?.toFixed(0)}ms</td>
                            <td className="px-4 py-3 text-zinc-600 whitespace-nowrap">
                              <TimeAgo ts={q.timestamp} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Chunks Tab */}
            {activeTab === "chunks" && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Filter by filename…"
                    value={chunkFilter}
                    onChange={(e) => setChunkFilter(e.target.value)}
                    className="bg-zinc-900/80 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-sky-500/50 w-64"
                  />
                  <span className="text-xs text-zinc-600">{filteredChunks.length} chunks shown</span>
                  {quarantinedCount > 0 && (
                    <span className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 px-2 py-1 rounded-lg">
                      ⚠ {quarantinedCount} quarantined
                    </span>
                  )}
                </div>
                <div className="overflow-x-auto rounded-xl border border-zinc-800">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900/80">
                        <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Chunk ID</th>
                        <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Source</th>
                        <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Index</th>
                        <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Characters</th>
                        <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900">
                      {filteredChunks.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-10 text-center text-zinc-600">No chunks indexed yet.</td>
                        </tr>
                      ) : (
                        filteredChunks.map((c) => (
                          <tr key={c.chunk_id} className={`hover:bg-zinc-900/40 transition-colors ${c.is_quarantined || c.is_poisoned ? "bg-red-500/5" : ""}`}>
                            <td className="px-4 py-2.5 font-mono text-zinc-600 max-w-32 truncate" title={c.chunk_id}>{c.chunk_id.slice(0, 12)}…</td>
                            <td className="px-4 py-2.5 text-sky-400">{c.source_filename}</td>
                            <td className="px-4 py-2.5 text-zinc-500">{c.chunk_index}</td>
                            <td className="px-4 py-2.5 text-zinc-500 tabular-nums">{c.character_count?.toLocaleString()}</td>
                            <td className="px-4 py-2.5">
                              {c.is_quarantined || c.is_poisoned ? (
                                <span className="text-red-300 bg-red-500/15 border border-red-500/30 px-2 py-0.5 rounded text-xs font-bold">
                                  {c.is_poisoned ? "POISONED" : "QUARANTINED"}
                                </span>
                              ) : (
                                <span className="text-emerald-400 text-xs font-medium">✓ Clean</span>
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

            {/* Ingestions Tab */}
            {activeTab === "ingestions" && (
              <div className="space-y-3">
                {!audit?.recent_ingestions?.length ? (
                  <div className="text-center py-16 text-zinc-600 text-sm">No documents ingested yet.</div>
                ) : (
                  <div className="overflow-x-auto rounded-xl border border-zinc-800">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-zinc-800 bg-zinc-900/80">
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Filename</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Type</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Characters</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">Chunks</th>
                          <th className="text-left px-4 py-3 text-zinc-500 font-semibold uppercase tracking-wider">When</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900">
                        {audit.recent_ingestions.map((ing, i) => (
                          <tr key={i} className="hover:bg-zinc-900/40 transition-colors">
                            <td className="px-4 py-3 text-sky-400 font-medium">{ing.filename}</td>
                            <td className="px-4 py-3 text-zinc-500 uppercase font-mono">{ing.file_type}</td>
                            <td className="px-4 py-3 text-zinc-500 tabular-nums">{ing.character_count?.toLocaleString()}</td>
                            <td className="px-4 py-3 text-zinc-300 font-bold">{ing.chunks_created}</td>
                            <td className="px-4 py-3 text-zinc-600 whitespace-nowrap"><TimeAgo ts={ing.timestamp} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </main>

      <footer className="border-t border-zinc-900 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 text-xs text-zinc-700">
          SENTINEL Admin Console · Phase 4: Trust & Security Integrated · v{stats?.system_version ?? "0.4.0"}
        </div>
      </footer>
    </div>
  );
}

