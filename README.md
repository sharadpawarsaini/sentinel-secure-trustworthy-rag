# SENTINEL: A Secure and Trustworthy RAG System

<p align="center">
  <img src="https://img.shields.io/badge/Project-SENTINEL-1E3A8A?style=for-the-badge&logo=shield" alt="SENTINEL Logo" />
</p>

<p align="center">
  <em>A Secure and Trustworthy Retrieval-Augmented Generation System with Multi-Layer Prompt Injection Defense, Document Poisoning Quarantine, and Evidence-Grounded Hallucination Mitigation.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Phase%201-Research%20Completed-success?style=flat-square" alt="Phase 1" />
  <img src="https://img.shields.io/badge/Phase%202-Baseline%20RAG%20Operational-success?style=flat-square" alt="Phase 2" />
  <img src="https://img.shields.io/badge/Tests-26%20Passing%20(100%25)-emerald?style=flat-square" alt="Tests" />
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/VectorDB-ChromaDB-purple?style=flat-square" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/Embeddings-MiniLM--L6--v2-orange?style=flat-square" alt="MiniLM" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
</p>

---

## 📌 Core Principle

> ### **"Secure the Context. Verify the Answer. Trust the Output."**

SENTINEL is an academic research-oriented system designed to investigate and resolve the fundamental vulnerabilities of Retrieval-Augmented Generation (RAG):
1. **Adversarial Exploitation**: Direct prompt injection, indirect prompt injection concealed inside retrieved passages, and corpus/knowledge-base poisoning.
2. **Epistemic Unreliability**: Intrinsic and extrinsic hallucinations where the LLM asserts ungrounded claims absent from the retrieved evidence.
3. **Absence of Trust Measurement**: Failure to quantify evidential support, leading models to emit confabulated answers instead of principled abstention.

---

## 🖥️ Live Web Application Interface

Below is an authentic visual preview of the operational SENTINEL web portal in action, illustrating real-time document ingestion, query execution, and verifiable evidence inspection:

<p align="center">
  <img src="docs/assets/web_portal_preview.svg" alt="SENTINEL Live Web Portal Interface" width="100%" />
</p>

---

## 📊 Automated Test Suite Results (100% Passing)

Every component is independently tested and verified through automated test suites in pytest. All 26 unit and integration tests are passing with zero failures:

<p align="center">
  <img src="docs/assets/test_coverage_chart.svg" alt="SENTINEL Test Suite Results" width="100%" />
</p>

### Detailed Component Verification Matrix

| Component | Test File | Verified Capabilities | Status |
| :--- | :--- | :--- | :--- |
| **2.2: Document Loader** | [`tests/unit/test_document_loader.py`](tests/unit/test_document_loader.py) | PDF, DOCX, TXT extraction, byte streams, carriage return cleaning, null-byte stripping, metadata preservation. | **5 / 5 Passed** |
| **2.3: Deterministic Chunker** | [`tests/unit/test_chunker.py`](tests/unit/test_chunker.py) | Recursive splitting (`\n\n`, `\n`, sentence delimiters), overlap preservation, deterministic SHA-256 chunk IDs, offset tracking. | **5 / 5 Passed** |
| **2.4: Dense Embedder** | [`tests/unit/test_embedder.py`](tests/unit/test_embedder.py) | Hugging Face `all-MiniLM-L6-v2` 384-d vectors, lazy singleton loading, batch encoding, semantic cosine distance ranking. | **4 / 4 Passed** |
| **2.5: Persistent Vector Store** | [`tests/unit/test_vector_store.py`](tests/unit/test_vector_store.py) | Embedded ChromaDB persistent store, cosine space, top-$K$ semantic querying, threshold filtering, document deletion, stats. | **3 / 3 Passed** |
| **2.6: Baseline Generator** | [`tests/unit/test_generator.py`](tests/unit/test_generator.py) | Tagged source prompt assembly, multi-provider LLM adapter (Ollama `codellama`, MockLLM for CI), latency instrumentation. | **4 / 4 Passed** |
| **2.7: FastAPI REST API** | [`tests/unit/test_api.py`](tests/unit/test_api.py) | `/api/health`, `/api/documents/upload`, `/api/rag/query`, `/api/documents`, `/favicon.ico`, error boundaries. | **4 / 4 Passed** |
| **2.8: System A Lifecycle** | [`tests/unit/test_rag.py`](tests/unit/test_rag.py) | End-to-end integration test verifying complete unaugmented Baseline RAG pipeline as an immutable control benchmark. | **1 / 1 Passed** |
| **TOTAL** | **7 Test Modules** | **Full Pipeline Verification** | **26 / 26 Passed (100%)** |

---

## 🏗️ System Architecture & Data Flow

<p align="center">
  <img src="docs/assets/architecture_flow.svg" alt="SENTINEL Pipeline Flow" width="100%" />
</p>

### Pipeline Execution Flow

```mermaid
flowchart TD
    classDef inputStyle fill:#1E293B,stroke:#38BDF8,stroke-width:2px,color:#F8FAFC
    classDef secStyle fill:#7F1D1D,stroke:#EF4444,stroke-width:2px,color:#FEE2E2
    classDef ragStyle fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#DCFCE7
    classDef trustStyle fill:#701A75,stroke:#D946EF,stroke-width:2px,color:#FDF4FF
    classDef mitStyle fill:#7C2D12,stroke:#F97316,stroke-width:2px,color:#FFEDD5
    classDef passStyle fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#ECFDF5

    User([👤 User Query]):::inputStyle --> InputSec[🛡️ 1. Input Security Guard\n- Obfuscation Decoding\n- Injection Signature Scan]:::secStyle
    
    InputSec -->|Malicious / Jailbreak| BlockOut[🚫 Block Query & Log Threat]:::secStyle
    InputSec -->|Clean Query| Retrieval[🔍 2. RAG Semantic Retrieval\n- ChromaDB Top-K Search\n- Score Distribution]:::ragStyle
    
    Retrieval --> CtxSec[🛡️ 3. Context Security Guard\n- Indirect Injection Scan\n- Document Poison Check]:::secStyle
    
    CtxSec -->|Poisoned Chunks| Quarantine[⚠️ Quarantine Malicious Chunks]:::secStyle
    Quarantine --> GenContext[Compile Safe Context]:::ragStyle
    CtxSec -->|Clean Chunks| GenContext
    
    GenContext --> LLM[🤖 4. LLM Synthesis\nEvidence-Grounded Prompt]:::ragStyle
    LLM --> TrustEngine[⚖️ 5. Trust & Hallucination Engine\n- Retrieval Confidence\n- Claim Decomposition\n- Cross-Encoder NLI Entailment\n- Faithfulness & Relevance]:::trustStyle
    
    TrustEngine --> TrustDecision{Composite Trust\nScore >= Threshold?}:::trustStyle
    
    TrustDecision -->|HIGH TRUST| EgressSec[🔒 6. Egress Security Filter\n- System Prompt Leak Check\n- Data Exfiltration Scanner]:::secStyle
    EgressSec --> FinalAnswer([✅ Verified & Grounded Answer]):::passStyle
    
    TrustDecision -->|LOW TRUST| Mitigation[🔄 7. Adaptive Mitigation Engine]:::mitStyle
    Mitigation --> Reformulate[Query Reformulation]:::mitStyle
    Reformulate --> ReRetrieve[Secondary Re-Retrieval]:::mitStyle
    ReRetrieve --> ReGen[Guided Regeneration]:::mitStyle
    ReGen --> ReCheck{Trust Re-check\nPassed?}:::trustStyle
    
    ReCheck -->|Pass| EgressSec
    ReCheck -->|Fail| Abstain([🛑 Principled Abstention:\n'Insufficient Verified Evidence']):::mitStyle
```

---

## 🛡️ Multi-Layer Defense-in-Depth Model

SENTINEL establishes four defense barriers to protect every stage of query resolution:

```
                                  DEFENSE-IN-DEPTH MATRIX
                                  
  [Barrier 1: Ingestion Guard]  ──► Scans raw documents pre-indexing; quashes hidden prompts.
  [Barrier 2: Input Guard]      ──► Normalizes Base64/Unicode homoglyphs; blocks direct jailbreaks.
  [Barrier 3: Context Guard]    ──► Inspects top-K retrieved chunks; quarantines indirect injections.
  [Barrier 4: Egress Guard]     ──► Intercepts output leaks, credential dumps, and exfiltration links.
```

| Defense Barrier | Location | Inspection Method | Threats Defeated |
| :--- | :--- | :--- | :--- |
| **Barrier 1: Ingestion Scanner** | Pre-Indexing (Upload) | Structural parser, heuristic payload detector, hidden text identifier. | Document poisoning, embedded malicious instructions. |
| **Barrier 2: Input Guard** | Pre-Retrieval (Query) | Canonicalization, zero-width stripper, regex banks, jailbreak heuristics. | Direct prompt injections, roleplay overrides, delimiter hijacking. |
| **Barrier 3: Context Quarantine**| Post-Retrieval (Chunks) | Second-pass semantic security filter over top-$K$ retrieved vectors. | Indirect prompt injection payloads inside retrieved context. |
| **Barrier 4: Egress Filter** | Post-Generation (Output) | Regex token matching for leaked system prompts, credentials, markdown image tags. | Data exfiltration, system prompt extraction, credential leaks. |

---

## ⚖️ Trust & Hallucination Verification Engine

Rather than treating LLM generations as unquestioned ground truth, the Trust Engine evaluates answer factuality via three evidence signals:

```
                            COMPOSITE TRUST SCORING ARCHITECTURE
                            
    ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
    │ Retrieval Confidence │      │   NLI Faithfulness   │      │   Answer Relevance   │
    │  Score Margin & Sim  │      │  Claim Entailment %  │      │ Query-Answer Sim     │
    └──────────┬───────────┘      └──────────┬───────────┘      └──────────┬───────────┘
               │                             │                             │
               └──────────────────────┬──────┴─────────────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │   Composite Trust Score   │
                        │   Status: HIGH/MED/LOW    │
                        └───────────────────────────┘
```

### Mathematical Formulations

1. **Retrieval Confidence ($C_{\text{retrieval}}$)**:
   $$C_{\text{retrieval}} = \frac{1}{K} \sum_{i=1}^K s_i \cdot \exp(-\lambda (i-1))$$
   Where $s_i$ denotes the cosine similarity of chunk $i$, down-weighting lower ranked chunks with decay rate $\lambda$.

2. **Atomic Propositional Decomposition**:
   The draft answer $y$ is decomposed into a set of discrete propositional claims:
   $$C = \{c_1, c_2, \dots, c_m\}$$

3. **Directional NLI Claim Entailment**:
   Each claim $c_i$ is evaluated against retrieved context $K$ using a cross-encoder NLI model (`cross-encoder/nli-deberta-v3-small`):
   $$\text{NLI}(c_i, K) \in \{\text{Entailment}, \text{Neutral}, \text{Contradiction}\}$$

4. **Faithfulness Ratio ($S_{\text{faith}}$)**:
   $$S_{\text{faith}} = \frac{|\{c_i \in C \mid \text{NLI}(c_i, K) = \text{Entailment}\}|}{|C|}$$

5. **Composite Trust Score ($\text{TS}$)**:
   $$\text{TS} = w_1 \cdot C_{\text{retrieval}} + w_2 \cdot S_{\text{faith}} + w_3 \cdot S_{\text{rel}}$$
   - $\text{TS} \ge 0.75 \implies \textbf{HIGH TRUST}$ (Deliver response)
   - $0.50 \le \text{TS} < 0.75 \implies \textbf{MEDIUM TRUST}$ (Deliver with caveat annotations)
   - $\text{TS} < 0.50 \implies \textbf{LOW TRUST}$ (Trigger Adaptive Mitigation)

---

## 🔬 Four-Way Comparative Experimental Study

In Phase 6, SENTINEL will be evaluated through controlled scientific benchmarking across **four distinct system configurations**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               THE FOUR COMPARATIVE SYSTEMS                             │
├──────────────────┬─────────────────────────────────────────────┬───────────────────────┤
│ System           │ Architectural Pipeline Configuration        │ Research Purpose      │
├──────────────────┼─────────────────────────────────────────────┼───────────────────────┤
│ **A. Baseline**  │ Query ──► Retrieval ──► LLM ──► Answer      │ Control Group         │
├──────────────────┼─────────────────────────────────────────────┼───────────────────────┤
│ **B. RAG + Sec** │ Query ──► Security ──► Retrieval ──► LLM    │ Isolate Security Gain │
├──────────────────┼─────────────────────────────────────────────┼───────────────────────┤
│ **C. RAG + Trust**│ Query ──► Retrieval ──► LLM ──► Trust Engine│ Isolate Trust Gain    │
├──────────────────┼─────────────────────────────────────────────┼───────────────────────┤
│ **D. SENTINEL**  │ Complete Multi-Layer Security + RAG +       │ Unified Research      │
│                  │ Trust + Closed-Loop Mitigation + Abstention │ System Under Test     │
└──────────────────┴─────────────────────────────────────────────┴───────────────────────┘
```

---

## 🗺️ Six-Phase Implementation Roadmap

```mermaid
gantt
    title SENTINEL 6-Phase Research & Engineering Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Research & Specs
    Literature Review & Threat Modeling :done, p1_1, 2026-09-17, 1d
    Formal Specifications & Architecture :done, p1_2, 2026-09-17, 1d
    section Phase 2: Baseline RAG
    Document Extraction & Chunking     :done, p2_1, 2026-09-18, 2d
    ChromaDB Embeddings & Retrieval     :done, p2_2, 2026-09-20, 2d
    Baseline Web API & Control Tests    :done, p2_3, 2026-09-22, 1d
    section Phase 3: Security Layer
    Input Guard & Obfuscation Decoder   :active, p3_1, 2026-09-23, 3d
    Context Quarantine & Egress Filter  :p3_2, after p3_1, 3d
    section Phase 4: Trust & NLI
    Cross-Encoder Claim Entailment      :p4_1, after p3_2, 4d
    Composite Trust Scoring Engine      :p4_2, after p4_1, 3d
    section Phase 5: Mitigation Loop
    Query Reformulation & Re-retrieval  :p5_1, after p4_2, 3d
    Principled Abstention & Pipeline    :p5_2, after p5_1, 3d
    section Phase 6: Research Validation
    Comparative Benchmarks (A, B, C, D) :p6_1, after p5_2, 4d
    Ablations & Paper Reporting         :p6_2, after p6_1, 3d
```

---

## 👥 Four-Laptop Team Ownership & Git Workflow

```
                            GITHUB REPOSITORY
                                    │
                            sharadpawarsaini/
                      sentinel-secure-trustworthy-rag
                                    │
            ┌───────────────┬───────┴───────┬───────────────┐
            ▼               ▼               ▼               ▼
         Bhumika          Adhya          Anwesha          Sharad
       (feature/rag) (feature/security)(feature/trust)(feature/mitigation)
            │               │               │               │
            └───────────────┴───────┬───────┴───────────────┘
                                    ▼
                                 DEVELOP
                                    ▼
                                  MAIN
```

### Team Responsibility Matrix

| Member | Focus Domain | Git Branch | Module Path | Core Deliverables |
| :--- | :--- | :--- | :--- | :--- |
| **Bhumika** | **RAG Foundation** | `feature/rag` | `sentinel/rag/` | PDF/DOCX/TXT extraction, chunking, embeddings, ChromaDB interface, semantic retrieval, baseline prompt assembly. |
| **Adhya** | **Security Layer** | `feature/security` | `sentinel/security/` | Direct injection detector, Base64/Unicode de-obfuscator, document poison scanner, context indirect injection guard, egress filter. |
| **Anwesha** | **Trust & NLI** | `feature/trust` | `sentinel/trust/` | Retrieval confidence calculation, atomic claim extractor, cross-encoder NLI directional entailment, faithfulness ratio, composite trust scoring. |
| **Sharad** | **Architecture & Integration** | `feature/mitigation`<br>`feature/integration` | `sentinel/backend/`<br>`sentinel/mitigation/`<br>`sentinel/pipeline/` | FastAPI orchestration, query reformulation, secondary re-retrieval, regeneration, principled abstention, UI coordination, and benchmark harness. |

---

## 🚀 Quickstart: Running the Web Application

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/sharadpawarsaini/sentinel-secure-trustworthy-rag.git
cd sentinel-secure-trustworthy-rag

# Activate virtual environment
.\.venv\Scripts\activate.ps1

# (Optional) Install dependencies if setting up on a new laptop
uv pip install -r requirements.txt
```

### 2. Start the Live Server
```powershell
.\.venv\Scripts\uvicorn.exe sentinel.backend.api:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open in Browser
- **Web Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Run the Full Test Suite
```powershell
.\.venv\Scripts\pytest.exe tests/unit/ -v
```

---

## 🎓 Academic Defense / Viva Quick Reference

> **Question: "What is SENTINEL?"**
> 
> *"SENTINEL is a research-oriented Secure and Trustworthy RAG system designed to investigate prompt injection, document poisoning, and hallucination risks in retrieval-augmented generation. It combines security detection, evidence-based trust assessment, adaptive mitigation, and principled abstention into a unified pipeline. We first build a conventional RAG baseline and then incrementally add security, trust, and mitigation layers. Finally, we compare the different configurations through controlled experiments and ablation studies to measure their effectiveness, reliability, and performance."*

> **Question: "What is your actual contribution?"**
> 
> *"Our contribution is not simply building another chatbot or RAG application. We are designing and experimentally evaluating an integrated security-and-trust pipeline for RAG—including attack detection, context security, trust assessment, adaptive mitigation, and abstention—and studying the effect of each layer through baseline comparisons and ablation experiments."*

---

<p align="center">
  <b>SENTINEL Research Project</b> • Maintained by Sharad, Bhumika, Adhya & Anwesha
</p>
