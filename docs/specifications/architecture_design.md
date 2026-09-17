# SENTINEL — System Architecture & Technical Design

**Project:** SENTINEL: A Secure and Trustworthy RAG System with Multi-Layer Prompt Injection Defense and Hallucination Mitigation  
**Phase:** 1 — Research, Literature Review & Requirements  
**Target Milestone:** Detailed software architecture, component interfaces, state machine transitions, and data models.

---

## 1. High-Level Modular Decomposition

SENTINEL is structured as a decoupled, layered pipeline operating within a unified asynchronous Python framework (FastAPI) and connected to a Next.js diagnostic frontend.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION TIER                             │
│       Next.js / React Web UI — Diagnostic Inspector & Demo Portal      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / Server-Sent Events
┌───────────────────────────────────▼────────────────────────────────────┐
│                           API GATEWAY TIER                             │
│          FastAPI Server — Request Validation, Routing & Session        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    SENTINEL PIPELINE ORCHESTRATOR                      │
│             State Machine Coordinator & Mode Selector (A, B, C, D)     │
└───────┬─────────────────┬───────────────────┬───────────────────┬──────┘
        │                 │                   │                   │
        ▼                 ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   SECURITY   │   │     RAG      │   │    TRUST     │   │  MITIGATION  │
│    ENGINE    │   │    ENGINE    │   │    ENGINE    │   │    ENGINE    │
│  (Adhya)     │   │  (Bhumika)   │   │  (Anwesha)   │   │   (Sharad)   │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 2. Component Specifications & Interfaces

### 2.1 Security Engine (`sentinel.security`) — Owner: Adhya
- **Module `normalizer.py`**:
  - `normalize_text(raw_input: str) -> NormalizedResult`:
    1. Detects and decodes valid Base64 and Hexadecimal substrings.
    2. Maps Unicode confusable homoglyphs to Latin-1 ASCII equivalents (NFKD normalization).
    3. Strips non-printing Unicode characters (e.g., `\u200B` zero-width space, `\u200C` zero-width non-joiner).
- **Module `input_scanner.py`**:
  - `scan_input(normalized_text: str) -> SecurityVerdict`:
    - Evaluates input against signature banks and jailbreak heuristics.
    - Returns structured payload:
      ```python
      class SecurityVerdict(BaseModel):
          is_malicious: bool
          risk_score: float  # [0.0, 1.0]
          attack_type: Optional[str]  # e.g., "direct_prompt_injection", "jailbreak"
          matched_patterns: List[str]
          action: Literal["PASS", "BLOCK", "FLAG"]
      ```
- **Module `document_scanner.py`**:
  - `scan_chunk_for_poison(chunk_text: str) -> DocumentSecurityVerdict`:
    - Inspects raw text chunks during document upload.
    - Tags suspicious chunks as `is_quarantined=True` with audit reasons.
- **Module `context_scanner.py`**:
  - `filter_retrieved_context(chunks: List[RetrievedChunk]) -> ContextFilterResult`:
    - Scans top-$K$ chunks returned by the RAG engine for indirect prompt injection markers.
    - Returns safe chunks for generation and logs quarantined chunks for display.
- **Module `egress_scanner.py`**:
  - `scan_output(llm_output: str, system_prompt: str) -> EgressVerdict`:
    - Checks for output regurgitation of system prompts, leaked API keys (`sk-...`), or markdown data exfiltration tokens (`![]()`).

### 2.2 RAG Engine (`sentinel.rag`) — Owner: Bhumika
- **Module `document_loader.py`**:
  - `load_document(file_path: Path) -> LoadedDocument`:
    - Handles text extraction from `.pdf` (using `pypdf`), `.docx` (using `python-docx`), and `.txt`.
    - Preserves structural metadata: source filename, page index, and timestamps.
- **Module `chunker.py`**:
  - `chunk_document(doc: LoadedDocument, chunk_size: int = 512, chunk_overlap: int = 64) -> List[TextChunk]`:
    - Recursively splits by paragraphs, newlines, and sentence delimiters.
    - Calculates a deterministic SHA-256 hash for every chunk.
- **Module `embedder.py`**:
  - `get_embeddings(texts: List[str]) -> np.ndarray`:
    - Computes dense embeddings using `sentence-transformers` (default: `all-MiniLM-L6-v2`, 384-dimensional).
- **Module `vector_store.py`**:
  - `VectorStoreManager`:
    - Initializes and manages ChromaDB persistent collection on disk (`data/vectorstore`).
    - Methods: `add_chunks(chunks: List[TextChunk])`, `query_similar(query_text: str, top_k: int = 4) -> List[RetrievedChunk]`.
- **Module `generator.py`**:
  - `generate_answer(query: str, context_chunks: List[RetrievedChunk], system_prompt: str) -> GenerationResult`:
    - Formats retrieved chunks with bracketed identifiers `[Source 1: filename, p. X]`.
    - Submits structured prompt to LLM client (Ollama/OpenAI/Gemini).

### 2.3 Trust Engine (`sentinel.trust`) — Owner: Anwesha
- **Module `retrieval_confidence.py`**:
  - `compute_retrieval_confidence(chunks: List[RetrievedChunk]) -> float`:
    - Computes confidence $C_{\text{retrieval}} \in [0, 1]$ using cosine similarity scores:
      $$C_{\text{retrieval}} = \frac{1}{K} \sum_{i=1}^K s_i \cdot \exp(-\lambda (i-1))$$
- **Module `claim_extractor.py`**:
  - `extract_claims(generated_text: str) -> List[str]`:
    - Splits multi-sentence generation into atomic propositional statements.
- **Module `nli_verifier.py`**:
  - `verify_claim_entailment(claim: str, context_chunks: List[RetrievedChunk]) -> NLIClaimVerdict`:
    - Uses local cross-encoder NLI model (e.g., `cross-encoder/nli-deberta-v3-small`).
    - Produces logits for `[contradiction, neutral, entailment]`.
- **Module `composite_scorer.py`**:
  - `evaluate_trust(query: str, answer: str, chunks: List[RetrievedChunk]) -> TrustReport`:
    - Combines confidence, faithfulness ratio, and semantic relevance into a unified `TrustReport`.

### 2.4 Mitigation Engine (`sentinel.mitigation`) — Owner: Sharad
- **Module `reformulator.py`**:
  - `reformulate_query(original_query: str, failure_context: str) -> str`:
    - Rewrites query to eliminate ambiguity and optimize semantic search terms.
- **Module `re_retriever.py`**:
  - `re_retrieve(reformulated_query: str, top_k: int = 6) -> List[RetrievedChunk]`:
    - Executes expanded secondary search.
- **Module `regenerator.py`**:
  - `regenerate_with_constraints(query: str, new_chunks: List[RetrievedChunk]) -> str`:
    - Re-prompts generator with explicit instruction to strictly adhere to new context.
- **Module `abstention.py`**:
  - `generate_abstention(query: str, reason: str) -> AbstentionResult`:
    - Produces transparent abstention when trust cannot be established post-mitigation.

---

## 3. Pipeline State Machine

```
               [INIT: USER QUERY]
                        │
                        ▼
                [STATE: INPUT_SCAN]
                        │
             ┌──────────┴──────────┐
             │ Malicious           │ Clean
             ▼                     ▼
      [STATE: BLOCKED]     [STATE: RETRIEVAL]
                                   │
                                   ▼
                        [STATE: CONTEXT_SCAN]
                                   │
                         ┌─────────┴─────────┐
                         │ Poisoned Chunks   │ Clean Chunks
                         ▼                   ▼
                  [QUARANTINE]        [STATE: GENERATION]
                         │                   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                          [STATE: TRUST_EVAL]
                                   │
                         ┌─────────┴─────────┐
                         │ Trust >= tau      │ Trust < tau
                         ▼                   ▼
                 [STATE: EGRESS]     [STATE: MITIGATION]
                         │                   │
                         │ Clean             │ Re-retrieve & Regenerate
                         ▼                   ▼
                  [STATE: DELIVER]   [STATE: TRUST_RECHECK]
                                             │
                                   ┌─────────┴─────────┐
                                   │ Pass              │ Fail
                                   ▼                   ▼
                            [STATE: EGRESS]     [STATE: ABSTAIN]
```

---

## 4. Technology Stack Justification Matrix

| Component | Selected Technology | Alternative Evaluated | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.11) | Flask, Express.js | Native async support, Pydantic type safety, auto-generated OpenAPI documentation, seamless integration with Python ML/NLP stack. |
| **Vector Database** | **ChromaDB** | Qdrant, Pinecone | In-process persistent storage (SQLite/HNSW); zero external daemon overhead; enables frictionless local multi-laptop git clone execution. |
| **Embeddings** | **SentenceTransformers (`all-MiniLM-L6-v2`)** | OpenAI `text-embedding-3-small` | Fast local CPU execution ($< 20$ms per chunk), zero API cost, deterministic, reproducible for academic comparison. |
| **NLI Verification** | **Cross-Encoder (`nli-deberta-v3-small`)** | GPT-4o-mini as Judge | Deterministic logits, sub-second inference on CPU, eliminates non-deterministic judge hallucination loops. |
| **Frontend UI** | **Next.js 14 / Tailwind CSS** | Streamlit, Gradio | Full UI flexibility to render detailed pipeline telemetry, side-by-side comparative mode views, and inspection dashboards beyond rigid chat widgets. |
