"""Asset generation script to render vector SVG mockups and test charts for the README."""

import os
from pathlib import Path

ASSETS_DIR = Path("docs/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def generate_web_portal_svg():
    """Generate a vector screenshot mockup of the live SENTINEL web portal."""
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 700" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0ea5e9"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.6"/>
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="1100" height="700" rx="16" fill="url(#bgGrad)" stroke="#334155" stroke-width="2"/>

  <!-- Browser Window Header / Top Bar -->
  <rect x="0" y="0" width="1100" height="48" rx="16" fill="#0f172a"/>
  <rect x="0" y="32" width="1100" height="16" fill="#0f172a"/>
  <line x1="0" y1="48" x2="1100" y2="48" stroke="#1e293b" stroke-width="1.5"/>

  <!-- Mac-style Window Controls -->
  <circle cx="28" cy="24" r="6" fill="#ef4444"/>
  <circle cx="48" cy="24" r="6" fill="#eab308"/>
  <circle cx="68" cy="24" r="6" fill="#22c55e"/>

  <!-- Address Bar -->
  <rect x="300" y="10" width="500" height="28" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="550" y="28" fill="#94a3b8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" text-anchor="middle">http://127.0.0.1:8000 — SENTINEL Baseline RAG Portal</text>

  <!-- Portal Header Bar -->
  <rect x="24" y="64" width="1052" height="60" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
  
  <!-- Logo Icon -->
  <rect x="40" y="76" width="36" height="36" rx="8" fill="#0369a1" fill-opacity="0.3" stroke="#38bdf8" stroke-width="1.5"/>
  <path d="M58 82 L70 88 L70 98 C70 105 58 109 58 109 C58 109 46 105 46 98 L46 88 Z" fill="#0284c7" stroke="#ffffff" stroke-width="1.5"/>
  
  <!-- Portal Title -->
  <text x="88" y="94" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="16" font-weight="700" letter-spacing="1">SENTINEL</text>
  <rect x="180" y="80" width="145" height="22" rx="6" fill="#0284c7" fill-opacity="0.2" stroke="#38bdf8" stroke-width="1"/>
  <text x="252" y="95" fill="#38bdf8" font-family="monospace" font-size="11" font-weight="600" text-anchor="middle">Phase 2: Baseline RAG</text>

  <!-- Top Status Badges -->
  <rect x="740" y="80" width="105" height="26" rx="13" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <circle cx="754" cy="93" r="4" fill="#10b981"/>
  <text x="795" y="97" fill="#cbd5e1" font-family="monospace" font-size="11" text-anchor="middle">Connected</text>

  <rect x="855" y="80" width="110" height="26" rx="13" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="910" y="97" fill="#38bdf8" font-family="monospace" font-size="11" text-anchor="middle">LLM: codellama</text>

  <rect x="975" y="80" width="85" height="26" rx="13" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="1017" y="97" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="middle">109 Chunks</text>

  <!-- Notice Banner -->
  <rect x="24" y="136" width="1052" height="42" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
  <circle cx="44" cy="157" r="8" fill="#0284c7" fill-opacity="0.3"/>
  <text x="44" y="161" fill="#38bdf8" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">i</text>
  <text x="64" y="161" fill="#cbd5e1" font-family="-apple-system, sans-serif" font-size="12">
    <tspan fill="#ffffff" font-weight="600">Experimental Baseline RAG Mode: </tspan>
    Extract &rarr; Recursive Chunking &rarr; Dense Embedding &rarr; ChromaDB Top-K Search &rarr; Grounded Prompt &rarr; LLM Generation.
  </text>

  <!-- Left Column: Ingestion & Documents -->
  <rect x="24" y="190" width="340" height="485" rx="14" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#shadow)"/>
  
  <text x="44" y="222" fill="#ffffff" font-family="sans-serif" font-size="14" font-weight="600">Ingest Knowledge Document</text>
  
  <!-- Drop Zone -->
  <rect x="44" y="240" width="300" height="110" rx="10" fill="#020617" stroke="#334155" stroke-dasharray="6,6" stroke-width="1.5"/>
  <path d="M194 280 L194 265 M194 265 L186 273 M194 265 L202 273" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
  <text x="194" y="302" fill="#94a3b8" font-family="sans-serif" font-size="12" text-anchor="middle">corporate_handbook.pdf</text>
  <text x="194" y="322" fill="#10b981" font-family="monospace" font-size="11" text-anchor="middle">&#10003; 109 Chunks Indexed</text>

  <!-- Ingested Docs List -->
  <text x="44" y="380" fill="#ffffff" font-family="sans-serif" font-size="13" font-weight="600">Indexed Knowledge Documents</text>
  
  <rect x="44" y="396" width="300" height="44" rx="8" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <text x="56" y="423" fill="#cbd5e1" font-family="monospace" font-size="11">corporate_handbook.pdf</text>
  <rect x="260" y="408" width="70" height="20" rx="4" fill="#0369a1" fill-opacity="0.3"/>
  <text x="295" y="422" fill="#38bdf8" font-family="monospace" font-size="10" text-anchor="middle">109 chunks</text>

  <rect x="44" y="448" width="300" height="44" rx="8" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <text x="56" y="475" fill="#cbd5e1" font-family="monospace" font-size="11">executive_bios.txt</text>
  <rect x="260" y="460" width="70" height="20" rx="4" fill="#0369a1" fill-opacity="0.3"/>
  <text x="295" y="474" fill="#38bdf8" font-family="monospace" font-size="10" text-anchor="middle">4 chunks</text>

  <!-- Storage Details -->
  <rect x="44" y="520" width="300" height="135" rx="10" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <text x="56" y="545" fill="#94a3b8" font-family="sans-serif" font-size="11" font-weight="600">STORAGE ENGINE</text>
  <text x="56" y="570" fill="#cbd5e1" font-family="monospace" font-size="11">Store: ChromaDB (HNSW)</text>
  <text x="56" y="592" fill="#cbd5e1" font-family="monospace" font-size="11">Path: data/vectorstore</text>
  <text x="56" y="614" fill="#cbd5e1" font-family="monospace" font-size="11">Embed: all-MiniLM-L6-v2</text>
  <text x="56" y="636" fill="#10b981" font-family="monospace" font-size="11">Status: Persistent Online</text>

  <!-- Right Column: Query & Response Interface -->
  <rect x="380" y="190" width="696" height="485" rx="14" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#shadow)"/>

  <!-- Question Input Card -->
  <text x="404" y="222" fill="#ffffff" font-family="sans-serif" font-size="14" font-weight="600">Ask a Question</text>
  
  <rect x="404" y="238" width="648" height="60" rx="10" fill="#020617" stroke="#38bdf8" stroke-width="1.5"/>
  <text x="420" y="273" fill="#f8fafc" font-family="sans-serif" font-size="13">Who is the company CEO and how many days of paid vacation do employees receive?</text>

  <!-- Query Controls Row -->
  <text x="406" y="322" fill="#94a3b8" font-family="monospace" font-size="11">Top-K: 4</text>
  <text x="470" y="322" fill="#94a3b8" font-family="monospace" font-size="11">Backend: Ollama (codellama)</text>
  <rect x="940" y="306" width="112" height="28" rx="8" fill="url(#skyGrad)"/>
  <text x="996" y="324" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="600" text-anchor="middle">Ask Question</text>

  <!-- Generated Answer Container -->
  <rect x="404" y="348" width="648" height="110" rx="10" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <rect x="404" y="348" width="648" height="30" rx="10" fill="#1e293b"/>
  <text x="420" y="368" fill="#38bdf8" font-family="sans-serif" font-size="12" font-weight="700">GENERATED ANSWER</text>
  <text x="890" y="368" fill="#94a3b8" font-family="monospace" font-size="10">Model: codellama:latest | Latency: 1.1s</text>
  
  <text x="420" y="400" fill="#f1f5f9" font-family="sans-serif" font-size="12.5" font-weight="500">Based strictly on the provided context:</text>
  <text x="420" y="420" fill="#cbd5e1" font-family="sans-serif" font-size="12">1. The Chief Executive Officer (CEO) of the technology corporation is <tspan fill="#38bdf8" font-weight="600">John Smith</tspan>.</text>
  <text x="420" y="440" fill="#cbd5e1" font-family="sans-serif" font-size="12">2. All permanent employees are allocated <tspan fill="#38bdf8" font-weight="600">25 days</tspan> of annual paid vacation leave.</text>

  <!-- Evidence Chunks Header -->
  <text x="404" y="482" fill="#ffffff" font-family="sans-serif" font-size="13" font-weight="600">Retrieved Evidence Chunks (2)</text>
  <text x="965" y="482" fill="#94a3b8" font-family="monospace" font-size="10">Ranked by Cosine Sim</text>

  <!-- Evidence Chunk 1 -->
  <rect x="404" y="496" width="648" height="76" rx="8" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <rect x="416" y="506" width="65" height="18" rx="4" fill="#0284c7" fill-opacity="0.2"/>
  <text x="448.5" y="519" fill="#38bdf8" font-family="monospace" font-size="10" font-weight="600" text-anchor="middle">#1 Chunk</text>
  <text x="490" y="519" fill="#94a3b8" font-family="monospace" font-size="10">corporate_handbook.pdf [Index: 0]</text>
  <rect x="975" y="506" width="65" height="18" rx="4" fill="#10b981" fill-opacity="0.2"/>
  <text x="1007.5" y="519" fill="#10b981" font-family="monospace" font-size="10" font-weight="700" text-anchor="middle">Sim: 0.914</text>
  <text x="416" y="544" fill="#94a3b8" font-family="monospace" font-size="11">"The Chief Executive Officer (CEO) of the technology corporation is John Smith. He oversees global engineering..."</text>

  <!-- Evidence Chunk 2 -->
  <rect x="404" y="582" width="648" height="76" rx="8" fill="#020617" stroke="#1e293b" stroke-width="1"/>
  <rect x="416" y="592" width="65" height="18" rx="4" fill="#0284c7" fill-opacity="0.2"/>
  <text x="448.5" y="605" fill="#38bdf8" font-family="monospace" font-size="10" font-weight="600" text-anchor="middle">#2 Chunk</text>
  <text x="490" y="605" fill="#94a3b8" font-family="monospace" font-size="10">corporate_handbook.pdf [Index: 1]</text>
  <rect x="975" y="592" width="65" height="18" rx="4" fill="#10b981" fill-opacity="0.2"/>
  <text x="1007.5" y="605" fill="#10b981" font-family="monospace" font-size="10" font-weight="700" text-anchor="middle">Sim: 0.862</text>
  <text x="416" y="630" fill="#94a3b8" font-family="monospace" font-size="11">"All permanent employees are allocated 25 days of annual paid vacation leave. Unused leave carries over up to..."</text>

</svg>
"""
    file_path = ASSETS_DIR / "web_portal_preview.svg"
    file_path.write_text(svg_content.strip(), encoding="utf-8")
    print(f"Generated: {file_path}")


def generate_test_coverage_svg():
    """Generate visual test metric chart showing 26/26 tests passed."""
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 480" width="100%" height="100%">
  <defs>
    <linearGradient id="chartBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="greenBar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#10b981"/>
    </linearGradient>
  </defs>

  <!-- Background Canvas -->
  <rect width="900" height="480" rx="16" fill="url(#chartBg)" stroke="#334155" stroke-width="1.5"/>

  <!-- Header -->
  <text x="40" y="46" fill="#ffffff" font-family="-apple-system, sans-serif" font-size="18" font-weight="700">SENTINEL Phase 2 — Automated Test Suite Results</text>
  <text x="40" y="70" fill="#94a3b8" font-family="monospace" font-size="12">Framework: pytest 9.1.1 | Python 3.12.13 | Platform: Windows x86_64</text>
  
  <!-- Master Summary Badge -->
  <rect x="680" y="30" width="180" height="46" rx="8" fill="#064e3b" stroke="#10b981" stroke-width="1.5"/>
  <circle cx="704" cy="53" r="8" fill="#10b981"/>
  <text x="704" y="57" fill="#ffffff" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="middle">&#10003;</text>
  <text x="724" y="49" fill="#a7f3d0" font-family="sans-serif" font-size="11" font-weight="600">ALL SUITES PASSED</text>
  <text x="724" y="65" fill="#ffffff" font-family="monospace" font-size="13" font-weight="700">26 / 26 (100%)</text>

  <!-- Horizontal Divider -->
  <line x1="40" y1="92" x2="860" y2="92" stroke="#1e293b" stroke-width="1"/>

  <!-- Bar 1: Document Loader -->
  <text x="40" y="130" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.2: Document Loader (PDF/DOCX/TXT)</text>
  <text x="40" y="148" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_document_loader.py</text>
  <rect x="420" y="122" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="122" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="139" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">5 / 5 Passed</text>

  <!-- Bar 2: Text Chunker -->
  <text x="40" y="180" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.3: Deterministic Chunker (SHA-256)</text>
  <text x="40" y="198" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_chunker.py</text>
  <rect x="420" y="172" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="172" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="189" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">5 / 5 Passed</text>

  <!-- Bar 3: Dense Embeddings -->
  <text x="40" y="230" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.4: Dense Embedder (SentenceTransformer)</text>
  <text x="40" y="248" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_embedder.py</text>
  <rect x="420" y="222" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="222" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="239" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">4 / 4 Passed</text>

  <!-- Bar 4: Persistent ChromaDB -->
  <text x="40" y="280" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.5: Persistent ChromaDB Vector Store</text>
  <text x="40" y="298" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_vector_store.py</text>
  <rect x="420" y="272" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="272" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="289" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">3 / 3 Passed</text>

  <!-- Bar 5: Baseline Generator -->
  <text x="40" y="330" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.6: Baseline Generator &amp; LLM Adapter</text>
  <text x="40" y="348" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_generator.py</text>
  <rect x="420" y="322" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="322" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="339" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">4 / 4 Passed</text>

  <!-- Bar 6: FastAPI REST API -->
  <text x="40" y="380" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.7: FastAPI REST Endpoints &amp; UI</text>
  <text x="40" y="398" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_api.py</text>
  <rect x="420" y="372" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="372" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="389" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">4 / 4 Passed</text>

  <!-- Bar 7: Control Group Lifecycle -->
  <text x="40" y="430" fill="#e2e8f0" font-family="sans-serif" font-size="13" font-weight="600">Component 2.8: System A Baseline Control Lifecycle</text>
  <text x="40" y="448" fill="#64748b" font-family="monospace" font-size="11">tests/unit/test_rag.py</text>
  <rect x="420" y="422" width="360" height="24" rx="6" fill="#1e293b"/>
  <rect x="420" y="422" width="360" height="24" rx="6" fill="url(#greenBar)"/>
  <text x="795" y="439" fill="#10b981" font-family="monospace" font-size="12" font-weight="700">1 / 1 Passed</text>

</svg>
"""
    file_path = ASSETS_DIR / "test_coverage_chart.svg"
    file_path.write_text(svg_content.strip(), encoding="utf-8")
    print(f"Generated: {file_path}")


def generate_architecture_flow_svg():
    """Generate pipeline data flow vector diagram."""
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 420" width="100%" height="100%">
  <defs>
    <linearGradient id="blueCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0c4a6e"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <linearGradient id="darkBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>

  <rect width="1000" height="420" rx="16" fill="url(#darkBg)" stroke="#334155" stroke-width="1.5"/>

  <text x="40" y="40" fill="#ffffff" font-family="-apple-system, sans-serif" font-size="16" font-weight="700">SENTINEL — Baseline RAG Pipeline Architecture (System A)</text>
  <text x="40" y="60" fill="#94a3b8" font-family="monospace" font-size="11">End-to-End Data Flow: Multi-format Extraction &rarr; SHA-256 Chunker &rarr; ChromaDB HNSW &rarr; Grounded Prompt &rarr; LLM</text>

  <!-- Ingestion Flow Line -->
  <line x1="40" y1="80" x2="960" y2="80" stroke="#1e293b" stroke-width="1"/>

  <!-- Step 1: Document Upload -->
  <rect x="40" y="110" width="150" height="100" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="65" cy="135" r="12" fill="#0284c7" fill-opacity="0.3"/>
  <text x="65" y="140" fill="#38bdf8" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">1</text>
  <text x="85" y="140" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Doc Ingestion</text>
  <text x="55" y="165" fill="#94a3b8" font-family="monospace" font-size="10">PDF, DOCX, TXT</text>
  <text x="55" y="182" fill="#64748b" font-family="monospace" font-size="9">DocumentLoader</text>
  <text x="55" y="197" fill="#10b981" font-family="monospace" font-size="9">&#10003; Clean &amp; Metadata</text>

  <!-- Arrow 1 -> 2 -->
  <path d="M195 160 L225 160" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- Step 2: Deterministic Chunker -->
  <rect x="230" y="110" width="150" height="100" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="255" cy="135" r="12" fill="#0284c7" fill-opacity="0.3"/>
  <text x="255" y="140" fill="#38bdf8" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">2</text>
  <text x="275" y="140" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Text Chunker</text>
  <text x="245" y="165" fill="#94a3b8" font-family="monospace" font-size="10">Recursive 500c/50c</text>
  <text x="245" y="182" fill="#64748b" font-family="monospace" font-size="9">TextChunker</text>
  <text x="245" y="197" fill="#10b981" font-family="monospace" font-size="9">&#10003; SHA-256 Hashes</text>

  <!-- Arrow 2 -> 3 -->
  <path d="M385 160 L415 160" stroke="#38bdf8" stroke-width="2"/>

  <!-- Step 3: Embeddings -->
  <rect x="420" y="110" width="150" height="100" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="445" cy="135" r="12" fill="#0284c7" fill-opacity="0.3"/>
  <text x="445" y="140" fill="#38bdf8" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">3</text>
  <text x="465" y="140" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Embedder</text>
  <text x="435" y="165" fill="#94a3b8" font-family="monospace" font-size="10">all-MiniLM-L6-v2</text>
  <text x="435" y="182" fill="#64748b" font-family="monospace" font-size="9">SentenceTransformer</text>
  <text x="435" y="197" fill="#10b981" font-family="monospace" font-size="9">&#10003; 384-d Dense Vecs</text>

  <!-- Arrow 3 -> 4 -->
  <path d="M575 160 L605 160" stroke="#38bdf8" stroke-width="2"/>

  <!-- Step 4: ChromaDB Store -->
  <rect x="610" y="110" width="160" height="100" rx="12" fill="#0f172a" stroke="#a855f7" stroke-width="1.5"/>
  <circle cx="635" cy="135" r="12" fill="#7e22ce" fill-opacity="0.3"/>
  <text x="635" y="140" fill="#c084fc" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">4</text>
  <text x="655" y="140" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">ChromaDB</text>
  <text x="625" y="165" fill="#94a3b8" font-family="monospace" font-size="10">HNSW Cosine Space</text>
  <text x="625" y="182" fill="#64748b" font-family="monospace" font-size="9">VectorStoreManager</text>
  <text x="625" y="197" fill="#10b981" font-family="monospace" font-size="9">&#10003; Persistent Storage</text>

  <!-- Query Pipeline (Row 2) -->
  <!-- Step 5: User Query -->
  <rect x="40" y="270" width="150" height="100" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="65" cy="295" r="12" fill="#0284c7" fill-opacity="0.3"/>
  <text x="65" y="300" fill="#38bdf8" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">5</text>
  <text x="85" y="300" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">User Query</text>
  <text x="55" y="325" fill="#94a3b8" font-family="monospace" font-size="10">Natural Language</text>
  <text x="55" y="342" fill="#64748b" font-family="monospace" font-size="9">FastAPI: /api/rag/query</text>
  <text x="55" y="357" fill="#10b981" font-family="monospace" font-size="9">&#10003; Top-K Configurable</text>

  <!-- Arrow 5 -> Vector Search -->
  <path d="M195 320 L610 180" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4"/>

  <!-- Step 6: Evidence Retrieval -->
  <rect x="420" y="270" width="150" height="100" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="445" cy="295" r="12" fill="#0284c7" fill-opacity="0.3"/>
  <text x="445" y="300" fill="#38bdf8" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">6</text>
  <text x="465" y="300" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Top-K Chunks</text>
  <text x="435" y="325" fill="#94a3b8" font-family="monospace" font-size="10">Cosine Similarity</text>
  <text x="435" y="342" fill="#64748b" font-family="monospace" font-size="9">RetrievedChunk Models</text>
  <text x="435" y="357" fill="#10b981" font-family="monospace" font-size="9">&#10003; Provenance Chunks</text>

  <!-- Arrow 6 -> Generator -->
  <path d="M575 320 L610 320" stroke="#38bdf8" stroke-width="2"/>

  <!-- Step 7: Generator & LLM -->
  <rect x="610" y="270" width="160" height="100" rx="12" fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
  <circle cx="635" cy="295" r="12" fill="#064e3b" fill-opacity="0.5"/>
  <text x="635" y="300" fill="#34d399" font-family="monospace" font-size="12" font-weight="bold" text-anchor="middle">7</text>
  <text x="655" y="300" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Baseline Gen</text>
  <text x="625" y="325" fill="#94a3b8" font-family="monospace" font-size="10">Prompt Assembly</text>
  <text x="625" y="342" fill="#64748b" font-family="monospace" font-size="9">Ollama / Mock LLM</text>
  <text x="625" y="357" fill="#10b981" font-family="monospace" font-size="9">&#10003; Grounded Answer</text>

  <!-- Final Output Badge -->
  <rect x="810" y="270" width="150" height="100" rx="12" fill="#0369a1" fill-opacity="0.2" stroke="#38bdf8" stroke-width="1.5"/>
  <circle cx="835" cy="295" r="12" fill="#0284c7"/>
  <text x="835" y="300" fill="#ffffff" font-family="sans-serif" font-size="11" font-weight="bold" text-anchor="middle">&#10003;</text>
  <text x="855" y="300" fill="#ffffff" font-family="sans-serif" font-size="12" font-weight="700">Output Delivery</text>
  <text x="825" y="325" fill="#e0f2fe" font-family="monospace" font-size="10">Web UI / REST API</text>
  <text x="825" y="342" fill="#7dd3fc" font-family="monospace" font-size="9">Answer + Provenance</text>
  <text x="825" y="357" fill="#10b981" font-family="monospace" font-size="9">&#10003; Auditable Citations</text>

  <path d="M775 320 L805 320" stroke="#38bdf8" stroke-width="2"/>

</svg>
"""
    file_path = ASSETS_DIR / "architecture_flow.svg"
    file_path.write_text(svg_content.strip(), encoding="utf-8")
    print(f"Generated: {file_path}")


def generate_admin_panel_svg():
    """Generate a vector mockup of the executive Phase 2 Admin Observability Console."""
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 720" width="100%" height="100%">
  <defs>
    <linearGradient id="adminBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="100%" stop-color="#090d16"/>
    </linearGradient>
    <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
    <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>
    <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="1150" height="720" rx="16" fill="url(#adminBg)" stroke="#1e293b" stroke-width="2"/>

  <!-- Window Chrome Header -->
  <rect x="0" y="0" width="1150" height="44" rx="16" fill="#0f172a"/>
  <rect x="0" y="28" width="1150" height="16" fill="#0f172a"/>
  <line x1="0" y1="44" x2="1150" y2="44" stroke="#1e293b" stroke-width="1.5"/>

  <!-- Window Controls -->
  <circle cx="28" cy="22" r="5.5" fill="#ef4444"/>
  <circle cx="46" cy="22" r="5.5" fill="#eab308"/>
  <circle cx="64" cy="22" r="5.5" fill="#22c55e"/>

  <!-- URL Bar -->
  <rect x="325" y="8" width="500" height="28" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="575" y="26" fill="#94a3b8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" text-anchor="middle">http://127.0.0.1:8000/admin — SENTINEL Phase 2 Admin Console</text>

  <!-- Console Header Bar -->
  <rect x="24" y="58" width="1102" height="64" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
  
  <!-- Icon & Brand Title -->
  <rect x="40" y="72" width="36" height="36" rx="8" fill="#0e7490" fill-opacity="0.25" stroke="#06b6d4" stroke-width="1.5"/>
  <circle cx="58" cy="90" r="8" fill="none" stroke="#22d3ee" stroke-width="2.5"/>
  <circle cx="58" cy="90" r="3" fill="#22d3ee"/>
  
  <text x="88" y="90" fill="#ffffff" font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="15" font-weight="700" letter-spacing="0.5">SENTINEL ADMIN CONSOLE</text>
  <text x="88" y="106" fill="#64748b" font-family="-apple-system, sans-serif" font-size="11">Phase 2: Baseline RAG Activity Observability &amp; Telemetry</text>

  <rect x="360" y="78" width="130" height="24" rx="6" fill="#083344" stroke="#06b6d4" stroke-width="1"/>
  <text x="425" y="94" fill="#22d3ee" font-family="monospace" font-size="10.5" font-weight="600" text-anchor="middle">ADMINISTRATOR</text>

  <!-- Header Right Badges -->
  <rect x="830" y="76" width="130" height="28" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <circle cx="846" cy="90" r="4" fill="#10b981"/>
  <text x="906" y="94" fill="#cbd5e1" font-family="monospace" font-size="11" text-anchor="middle">System Online</text>

  <rect x="972" y="76" width="140" height="28" rx="8" fill="#0369a1" fill-opacity="0.2" stroke="#0284c7" stroke-width="1"/>
  <text x="1042" y="94" fill="#38bdf8" font-family="-apple-system, sans-serif" font-size="11.5" font-weight="600" text-anchor="middle">&larr; User Portal</text>

  <!-- 4 KPI Summary Cards -->
  <!-- Card 1: Total Indexed Chunks -->
  <rect x="24" y="136" width="260" height="96" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#cardShadow)"/>
  <text x="44" y="162" fill="#64748b" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">INDEXED CHUNKS</text>
  <text x="44" y="200" fill="#ffffff" font-family="monospace" font-size="28" font-weight="700">109</text>
  <rect x="232" y="152" width="36" height="36" rx="8" fill="#083344" stroke="#06b6d4" stroke-width="1"/>
  <circle cx="250" cy="170" r="6" fill="#06b6d4"/>
  <text x="44" y="218" fill="#06b6d4" font-family="monospace" font-size="10">1 unique document</text>

  <!-- Card 2: Query Transactions -->
  <rect x="304" y="136" width="260" height="96" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#cardShadow)"/>
  <text x="324" y="162" fill="#64748b" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">QUERY TRANSACTIONS</text>
  <text x="324" y="200" fill="#ffffff" font-family="monospace" font-size="28" font-weight="700">18</text>
  <rect x="512" y="152" width="36" height="36" rx="8" fill="#052e16" stroke="#10b981" stroke-width="1"/>
  <circle cx="530" cy="170" r="6" fill="#10b981"/>
  <text x="324" y="218" fill="#10b981" font-family="monospace" font-size="10">Circular audit buffer</text>

  <!-- Card 3: Avg Roundtrip Latency -->
  <rect x="584" y="136" width="260" height="96" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#cardShadow)"/>
  <text x="604" y="162" fill="#64748b" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">AVG LATENCY (ROUNDTRIP)</text>
  <text x="604" y="200" fill="#ffffff" font-family="monospace" font-size="28" font-weight="700">1,180<tspan font-size="16" fill="#94a3b8"> ms</tspan></text>
  <rect x="792" y="152" width="36" height="36" rx="8" fill="#3b0764" stroke="#a855f7" stroke-width="1"/>
  <circle cx="810" cy="170" r="6" fill="#a855f7"/>
  <text x="604" y="218" fill="#c084fc" font-family="monospace" font-size="10">Min: 42ms | Max: 1,840ms</text>

  <!-- Card 4: Active Generator -->
  <rect x="864" y="136" width="262" height="96" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#cardShadow)"/>
  <text x="884" y="162" fill="#64748b" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" letter-spacing="0.5">ACTIVE GENERATION LLM</text>
  <text x="884" y="196" fill="#ffffff" font-family="monospace" font-size="19" font-weight="700">codellama:latest</text>
  <rect x="1074" y="152" width="36" height="36" rx="8" fill="#451a03" stroke="#f59e0b" stroke-width="1"/>
  <circle cx="1092" cy="170" r="6" fill="#f59e0b"/>
  <text x="884" y="218" fill="#f59e0b" font-family="monospace" font-size="10">Provider: Ollama Local</text>

  <!-- Navigation Tabs -->
  <rect x="24" y="246" width="1102" height="42" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
  
  <rect x="32" y="252" width="190" height="30" rx="8" fill="#0284c7" fill-opacity="0.25" stroke="#38bdf8" stroke-width="1"/>
  <text x="127" y="271" fill="#38bdf8" font-family="-apple-system, sans-serif" font-size="12" font-weight="600" text-anchor="middle">Query Audit Trail (18)</text>

  <rect x="232" y="252" width="210" height="30" rx="8" fill="#1e293b"/>
  <text x="337" y="271" fill="#94a3b8" font-family="-apple-system, sans-serif" font-size="12" text-anchor="middle">Corpus &amp; Chunk Explorer</text>

  <rect x="452" y="252" width="180" height="30" rx="8" fill="#1e293b"/>
  <text x="542" y="271" fill="#94a3b8" font-family="-apple-system, sans-serif" font-size="12" text-anchor="middle">System Diagnostics</text>

  <!-- Query Audit Trail Table Panel -->
  <rect x="24" y="302" width="1102" height="395" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" filter="url(#cardShadow)"/>

  <!-- Table Header -->
  <rect x="25" y="303" width="1100" height="38" rx="11" fill="#1e293b"/>
  <text x="44" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">TIMESTAMP (UTC)</text>
  <text x="180" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">USER QUERY PROMPT</text>
  <text x="640" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">INFERENCE ENGINE</text>
  <text x="800" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">TOP-K</text>
  <text x="880" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">TOP SIM</text>
  <text x="970" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">LATENCY</text>
  <text x="1060" y="327" fill="#94a3b8" font-family="monospace" font-size="11" font-weight="600">STATUS</text>

  <!-- Row 1 -->
  <line x1="25" y1="385" x2="1125" y2="385" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="367" fill="#64748b" font-family="monospace" font-size="11">20:23:14</text>
  <text x="180" y="367" fill="#e2e8f0" font-family="-apple-system, sans-serif" font-size="12">Who is the company CEO and what are the vacation days?</text>
  <rect x="640" y="352" width="140" height="22" rx="4" fill="#083344"/>
  <text x="710" y="367" fill="#38bdf8" font-family="monospace" font-size="10.5" text-anchor="middle">codellama:latest</text>
  <text x="815" y="367" fill="#94a3b8" font-family="monospace" font-size="11">4</text>
  <rect x="880" y="352" width="60" height="22" rx="4" fill="#052e16"/>
  <text x="910" y="367" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">0.914</text>
  <text x="970" y="367" fill="#cbd5e1" font-family="monospace" font-size="11">1,240 ms</text>
  <rect x="1055" y="352" width="55" height="22" rx="4" fill="#052e16"/>
  <text x="1082.5" y="367" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">200 OK</text>

  <!-- Row 2 -->
  <line x1="25" y1="432" x2="1125" y2="432" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="413" fill="#64748b" font-family="monospace" font-size="11">20:21:40</text>
  <text x="180" y="413" fill="#e2e8f0" font-family="-apple-system, sans-serif" font-size="12">Summarize the core technical findings from the interaction report.</text>
  <rect x="640" y="398" width="140" height="22" rx="4" fill="#083344"/>
  <text x="710" y="413" fill="#38bdf8" font-family="monospace" font-size="10.5" text-anchor="middle">codellama:latest</text>
  <text x="815" y="413" fill="#94a3b8" font-family="monospace" font-size="11">4</text>
  <rect x="880" y="398" width="60" height="22" rx="4" fill="#052e16"/>
  <text x="910" y="413" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">0.887</text>
  <text x="970" y="413" fill="#cbd5e1" font-family="monospace" font-size="11">1,412 ms</text>
  <rect x="1055" y="398" width="55" height="22" rx="4" fill="#052e16"/>
  <text x="1082.5" y="413" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">200 OK</text>

  <!-- Row 3 -->
  <line x1="25" y1="479" x2="1125" y2="479" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="459" fill="#64748b" font-family="monospace" font-size="11">20:18:02</text>
  <text x="180" y="459" fill="#e2e8f0" font-family="-apple-system, sans-serif" font-size="12">What are the primary security challenges in RAG systems?</text>
  <rect x="640" y="444" width="140" height="22" rx="4" fill="#1e1b4b"/>
  <text x="710" y="459" fill="#a5b4fc" font-family="monospace" font-size="10.5" text-anchor="middle">mock-baseline-llm</text>
  <text x="815" y="459" fill="#94a3b8" font-family="monospace" font-size="11">3</text>
  <rect x="880" y="444" width="60" height="22" rx="4" fill="#052e16"/>
  <text x="910" y="459" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">0.824</text>
  <text x="970" y="459" fill="#cbd5e1" font-family="monospace" font-size="11">46 ms</text>
  <rect x="1055" y="444" width="55" height="22" rx="4" fill="#052e16"/>
  <text x="1082.5" y="459" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">200 OK</text>

  <!-- Row 4 -->
  <line x1="25" y1="526" x2="1125" y2="526" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="505" fill="#64748b" font-family="monospace" font-size="11">20:15:28</text>
  <text x="180" y="505" fill="#e2e8f0" font-family="-apple-system, sans-serif" font-size="12">Explain the vector index structure and embedding dimensions.</text>
  <rect x="640" y="490" width="140" height="22" rx="4" fill="#083344"/>
  <text x="710" y="505" fill="#38bdf8" font-family="monospace" font-size="10.5" text-anchor="middle">codellama:latest</text>
  <text x="815" y="505" fill="#94a3b8" font-family="monospace" font-size="11">4</text>
  <rect x="880" y="490" width="60" height="22" rx="4" fill="#052e16"/>
  <text x="910" y="505" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">0.931</text>
  <text x="970" y="505" fill="#cbd5e1" font-family="monospace" font-size="11">1,090 ms</text>
  <rect x="1055" y="490" width="55" height="22" rx="4" fill="#052e16"/>
  <text x="1082.5" y="505" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">200 OK</text>

  <!-- Row 5 -->
  <line x1="25" y1="573" x2="1125" y2="573" stroke="#1e293b" stroke-width="1"/>
  <text x="44" y="551" fill="#64748b" font-family="monospace" font-size="11">20:12:11</text>
  <text x="180" y="551" fill="#e2e8f0" font-family="-apple-system, sans-serif" font-size="12">List the project deliverables for the industrial training term.</text>
  <rect x="640" y="536" width="140" height="22" rx="4" fill="#083344"/>
  <text x="710" y="551" fill="#38bdf8" font-family="monospace" font-size="10.5" text-anchor="middle">codellama:latest</text>
  <text x="815" y="551" fill="#94a3b8" font-family="monospace" font-size="11">4</text>
  <rect x="880" y="536" width="60" height="22" rx="4" fill="#052e16"/>
  <text x="910" y="551" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">0.899</text>
  <text x="970" y="551" fill="#cbd5e1" font-family="monospace" font-size="11">1,320 ms</text>
  <rect x="1055" y="536" width="55" height="22" rx="4" fill="#052e16"/>
  <text x="1082.5" y="551" fill="#10b981" font-family="monospace" font-size="10.5" font-weight="700" text-anchor="middle">200 OK</text>

  <!-- Table Footer / Telemetry status -->
  <rect x="25" y="650" width="1100" height="46" rx="10" fill="#020617"/>
  <text x="44" y="678" fill="#64748b" font-family="monospace" font-size="11">Showing recent 5 of 18 recorded transactions &bull; Audit storage: thread-safe circular buffer (200 records max)</text>
  <rect x="990" y="660" width="120" height="26" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="1050" y="677" fill="#94a3b8" font-family="sans-serif" font-size="11" text-anchor="middle">Export JSON Log</text>

</svg>
"""
    file_path = ASSETS_DIR / "admin_panel_preview.svg"
    file_path.write_text(svg_content.strip(), encoding="utf-8")
    print(f"Generated: {file_path}")


if __name__ == "__main__":
    generate_web_portal_svg()
    generate_test_coverage_svg()
    generate_architecture_flow_svg()
    generate_admin_panel_svg()
