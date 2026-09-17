# SENTINEL — Empirical Evaluation Plan & Research Protocol

**Project:** SENTINEL: A Secure and Trustworthy RAG System with Multi-Layer Prompt Injection Defense and Hallucination Mitigation  
**Phase:** 1 — Research, Literature Review & Requirements  
**Target Milestone:** Rigorous experimental methodology, 4-way comparative system definitions, dataset schemas, metrics, and ablation specifications.

---

## 1. Experimental Methodology & Comparative Framework

To answer the core research questions (RQ1–RQ4), SENTINEL will be evaluated via a controlled, 4-way comparative study across identical test datasets and execution environments.

### 1.1 The Four System Configurations

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FOUR SYSTEMS TO COMPARE                         │
├───────────────────┬────────────────────────────────────────────────────┤
│ Configuration     │ Architecture Pipeline                              │
├───────────────────┼────────────────────────────────────────────────────┤
│ A. Baseline RAG   │ Query ──► Retrieval ──► LLM ──► Answer             │
├───────────────────┼────────────────────────────────────────────────────┤
│ B. RAG + Security │ Query ──► Security ──► Retrieval ──► LLM ──► Answer│
├───────────────────┼────────────────────────────────────────────────────┤
│ C. RAG + Trust    │ Query ──► Retrieval ──► LLM ──► Trust ──► Answer   │
├───────────────────┼────────────────────────────────────────────────────┤
│ D. SENTINEL Full  │ Query ──► Input Sec ──► Retrieval ──► Context Sec  │
│                   │ ──► LLM ──► Trust ──► Mitigation (or Abstain)      │
│                   │ ──► Egress Sec ──► Verified Answer                 │
└───────────────────┴────────────────────────────────────────────────────┘
```

---

## 2. Benchmark Datasets

Evaluation will use a curated, versioned benchmark dataset stored under `tests/benchmarks/datasets/`.

### 2.1 Security Attack Benchmark (`injection_attacks.json`)
Consists of $N = 200$ evaluation instances evenly distributed across 5 test classes:
1. **Benign In-Domain Queries** ($n=80$): Complex, multi-sentence queries with technical jargon, system configuration questions, and edge-case punctuation to evaluate False Positive Rate (FPR).
2. **Direct Prompt Injection** ($n=30$): Instruction overrides, system prompt extraction, delimiter hijacking, and roleplay jailbreaks.
3. **Indirect Prompt Injection** ($n=30$): Benign questions queried against documents containing injected instructions in body text, footnotes, or appendices.
4. **Obfuscated Injections** ($n=30$): Injections encoded in Base64, Hexadecimal, Unicode Cyrillic homoglyphs, and zero-width character insertions.
5. **Document Poisoning Payloads** ($n=30$): Synthetically crafted poisoned documents designed to displace legitimate chunks through keyword stuffing and factual inversions.

### 2.2 Trust & Factuality Benchmark (`grounding_eval.json`)
Consists of $N = 100$ question-context pairs across 3 evidential categories:
1. **Fully Supported Pairs** ($n=50$): Context contains unambiguous, sufficient evidence directly answering the query.
2. **Partially Supported / Distractor Pairs** ($n=25$): Context touches on query entities but omits critical supporting claims, tempting the LLM to hallucinate missing facts.
3. **Unanswerable / Out-of-Corpus Queries** ($n=25$): Queries where the corpus contains no relevant evidence, testing the system's ability to recognize knowledge gaps and trigger principled abstention.

---

## 3. Mathematical Metric Definitions

All metrics will be computed deterministically from raw test execution logs.

### 3.1 Security Defense Metrics
- **Attack Detection Rate / Recall ($R_{\text{sec}}$)**:
  $$R_{\text{sec}} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
- **False Positive Rate ($\text{FPR}_{\text{sec}}$)**:
  $$\text{FPR}_{\text{sec}} = \frac{\text{FP}}{\text{FP} + \text{TN}}$$
- **Attack Success Rate ($\text{ASR}$)**:
  $$\text{ASR} = \frac{\text{Number of Successful Injections into Final Output}}{\text{Total Attack Injections Submitted}} \times 100\%$$
- **Precision ($P_{\text{sec}}$) and F1-Score ($F1_{\text{sec}}$)**:
  $$P_{\text{sec}} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad F1_{\text{sec}} = 2 \cdot \frac{P_{\text{sec}} \cdot R_{\text{sec}}}{P_{\text{sec}} + R_{\text{sec}}}$$

### 3.2 Trust & Grounding Metrics
- **Faithfulness Score ($S_{\text{faith}}$)**:
  $$S_{\text{faith}} = \frac{\sum_{i=1}^{|C|} \mathbb{I}(\text{NLI}(c_i, K) = \text{Entailment})}{|C|}$$
  Where $C$ is the set of extracted atomic claims from the generated answer and $K$ is the retrieved context.
- **Hallucination Rate ($\text{HR}$)**:
  $$\text{HR} = 1.0 - S_{\text{faith}}$$
- **Answer Relevance Score ($S_{\text{rel}}$)**: Cosine similarity between the embedding of the user query $\mathbf{e}_q$ and the generated answer $\mathbf{e}_y$.

### 3.3 Mitigation & Operational Efficiency Metrics
- **Mitigation Recovery Rate ($\text{MRR}$)**:
  $$\text{MRR} = \frac{\text{Queries transitioning from LOW Trust to HIGH/MEDIUM Trust}}{\text{Total Queries Triggering Mitigation}} \times 100\%$$
- **Abstention Precision ($\text{AP}$)**:
  $$\text{AP} = \frac{\text{Correct Abstentions on Unanswerable Queries}}{\text{Total System Abstentions}} \times 100\%$$
- **Pipeline Latency Overhead ($\Delta L$)**:
  $$\Delta L = L_{\text{SENTINEL}} - L_{\text{Baseline}}$$
  Partitioned into: $L_{\text{norm}}$, $L_{\text{input\_sec}}$, $L_{\text{retrieval}}$, $L_{\text{context\_sec}}$, $L_{\text{gen}}$, $L_{\text{trust}}$, and $L_{\text{mitigation}}$.

---

## 4. Ablation Study Protocol

To isolate the individual contribution of each defensive mechanism, we specify 4 systematic ablation experiments:

1. **Ablation 1: Remove Input Guard ($\text{SENTINEL} \setminus \text{InputSec}$)**:
   - Evaluates whether Context Quarantine and Egress Filtering alone can prevent direct injection attacks.
2. **Ablation 2: Remove Context Quarantine ($\text{SENTINEL} \setminus \text{ContextSec}$)**:
   - Measures how frequently indirect prompt injections embedded in retrieved chunks bypass the LLM and poison output.
3. **Ablation 3: Remove Mitigation Engine ($\text{SENTINEL} \setminus \text{Mitigation}$)**:
   - Measures the drop in factual recovery when the system merely blocks or accepts low-trust answers without dynamic reformulation.
4. **Ablation 4: Remove Principled Abstention ($\text{SENTINEL} \setminus \text{Abstain}$)**:
   - Forces generation on low-evidence context, measuring the resulting surge in hallucination rate.

---

## 5. Non-Fabrication Protocol & Data Integrity

> [!CAUTION]
> **Scientific Integrity Directive**:
> - Metric values must **never** be manually hard-coded or fabricated.
> - Automated benchmark runners (`run_security_eval.py` and `run_trust_eval.py`) will execute all test cases via API, write raw JSON records containing per-test timestamps, inputs, predictions, and elapsed milliseconds to `results/raw/`.
> - Plotting scripts (`generate_research_charts.py`) will parse only `results/raw/*.json` to compute summary tables and render Seaborn/Matplotlib graphs into `results/figures/`.
