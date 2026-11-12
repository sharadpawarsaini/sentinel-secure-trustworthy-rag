"""Master Closed-Loop Orchestrator for SENTINEL.

Integrates:
User Input -> Input Security -> Semantic Retrieval -> Context Security
-> LLM Generation -> Trust Evaluation -> Mitigation -> Egress Security -> Response/Abstain
Owned by: Sharad (Lead AI Engineer & System Architect)
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.rag.vector_store import VectorStoreManager, RetrievedChunk
from sentinel.rag.generator import BaselineGenerator, GenerationResult, get_llm_client
from sentinel.security.input_scanner import InputScanner, SecurityVerdict
from sentinel.security.context_scanner import ContextScanner, ContextSecurityReport
from sentinel.security.egress_scanner import EgressScanner, EgressVerdict
from sentinel.trust.composite_scorer import CompositeTrustScorer, TrustReport
from sentinel.trust.nli_verifier import NLIVerifier
from sentinel.mitigation.reformulator import QueryReformulator
from sentinel.mitigation.abstention import AbstentionEngine, AbstentionResult


class PipelineTelemetry(BaseModel):
    """Detailed timing and barrier telemetry for an executed pipeline query."""
    total_latency_ms: float
    input_scan_latency_ms: float
    retrieval_latency_ms: float
    context_scan_latency_ms: float
    generation_latency_ms: float
    trust_eval_latency_ms: float
    egress_scan_latency_ms: float
    mitigation_triggered: bool = False


class SentinelPipelineResult(BaseModel):
    """Unified result returned by the SENTINEL closed-loop RAG pipeline."""
    query: str
    answer: str
    is_abstained: bool = False
    abstention_reason: Optional[str] = None
    trust_score: float
    trust_verdict: str
    security_action: str
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    quarantined_chunks_count: int = 0
    security_verdict: SecurityVerdict
    context_security: ContextSecurityReport
    trust_report: Optional[TrustReport] = None
    egress_verdict: Optional[EgressVerdict] = None
    telemetry: PipelineTelemetry


class SentinelPipeline:
    """Master orchestrator for the SENTINEL Trust-Aware RAG Architecture."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreManager] = None,
        generator: Optional[BaselineGenerator] = None,
        input_scanner: Optional[InputScanner] = None,
        context_scanner: Optional[ContextScanner] = None,
        egress_scanner: Optional[EgressScanner] = None,
        trust_scorer: Optional[CompositeTrustScorer] = None,
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.generator = generator or BaselineGenerator(llm_client=get_llm_client())
        self.input_scanner = input_scanner or InputScanner()
        self.context_scanner = context_scanner or ContextScanner()
        self.egress_scanner = egress_scanner or EgressScanner()
        self.trust_scorer = trust_scorer or CompositeTrustScorer()

    def query(
        self,
        query_text: str,
        top_k: int = 4,
        enable_mitigation: bool = True
    ) -> SentinelPipelineResult:
        """Execute end-to-end multi-barrier query resolution."""
        start_time = time.perf_counter()

        # =====================================================================
        # BARRIER 1: Input Security Scanner
        # =====================================================================
        t0 = time.perf_counter()
        sec_verdict = self.input_scanner.scan(query_text)
        t_input = (time.perf_counter() - t0) * 1000

        if sec_verdict.action == "BLOCK":
            abstain_res = AbstentionEngine.security_block(sec_verdict.details)
            total_t = (time.perf_counter() - start_time) * 1000
            return SentinelPipelineResult(
                query=query_text,
                answer=abstain_res.user_message,
                is_abstained=True,
                abstention_reason=abstain_res.reason_code,
                trust_score=0.0,
                trust_verdict="BLOCKED_SECURITY_VIOLATION",
                security_action="BLOCK",
                retrieved_chunks=[],
                quarantined_chunks_count=0,
                security_verdict=sec_verdict,
                context_security=ContextSecurityReport(total_retrieved=0),
                trust_report=None,
                egress_verdict=None,
                telemetry=PipelineTelemetry(
                    total_latency_ms=round(total_t, 2),
                    input_scan_latency_ms=round(t_input, 2),
                    retrieval_latency_ms=0.0,
                    context_scan_latency_ms=0.0,
                    generation_latency_ms=0.0,
                    trust_eval_latency_ms=0.0,
                    egress_scan_latency_ms=0.0,
                    mitigation_triggered=False
                )
            )

        # =====================================================================
        # BARRIER 2: Dense Semantic Retrieval
        # =====================================================================
        t0 = time.perf_counter()
        raw_chunks = self.vector_store.query_similar(query_text, top_k=top_k)
        t_retrieval = (time.perf_counter() - t0) * 1000

        # =====================================================================
        # BARRIER 3: Retrieved-Context Security Scanner
        # =====================================================================
        t0 = time.perf_counter()
        context_report = self.context_scanner.filter_retrieved_context(raw_chunks)
        t_ctx_scan = (time.perf_counter() - t0) * 1000
        safe_chunks = context_report.safe_chunks

        # If zero safe chunks available, abstain cleanly
        if not safe_chunks:
            abstain_res = AbstentionEngine.insufficient_evidence(query_text, 0.0)
            total_t = (time.perf_counter() - start_time) * 1000
            return SentinelPipelineResult(
                query=query_text,
                answer=abstain_res.user_message,
                is_abstained=True,
                abstention_reason="INSUFFICIENT_EVIDENCE" if not raw_chunks else "CONTEXT_QUARANTINED",
                trust_score=0.0,
                trust_verdict="INSUFFICIENTLY_SUPPORTED",
                security_action=sec_verdict.action,
                retrieved_chunks=[],
                quarantined_chunks_count=len(context_report.quarantined_chunks),
                security_verdict=sec_verdict,
                context_security=context_report,
                trust_report=None,
                egress_verdict=None,
                telemetry=PipelineTelemetry(
                    total_latency_ms=round(total_t, 2),
                    input_scan_latency_ms=round(t_input, 2),
                    retrieval_latency_ms=round(t_retrieval, 2),
                    context_scan_latency_ms=round(t_ctx_scan, 2),
                    generation_latency_ms=0.0,
                    trust_eval_latency_ms=0.0,
                    egress_scan_latency_ms=0.0,
                    mitigation_triggered=False
                )
            )

        # =====================================================================
        # BARRIER 4: Delimiter-Isolated LLM Generation
        # =====================================================================
        t0 = time.perf_counter()
        gen_res = self.generator.generate(query_text, safe_chunks)
        t_gen = (time.perf_counter() - t0) * 1000
        candidate_answer = gen_res.answer

        # =====================================================================
        # BARRIER 5: Trust Evaluation & Hallucination Mitigation
        # =====================================================================
        t0 = time.perf_counter()
        trust_rep = self.trust_scorer.evaluate(query_text, candidate_answer, safe_chunks)
        t_trust = (time.perf_counter() - t0) * 1000
        mitigation_used = False

        # If verdict is POTENTIALLY_HALLUCINATED and mitigation is enabled, run closed-loop re-retrieval
        if trust_rep.verdict in ("POTENTIALLY_HALLUCINATED", "INSUFFICIENTLY_SUPPORTED") and enable_mitigation:
            mitigation_used = True
            reformulated_q = QueryReformulator.reformulate(query_text)
            new_raw_chunks = self.vector_store.query_similar(reformulated_q, top_k=top_k + 2)
            new_ctx_rep = self.context_scanner.filter_retrieved_context(new_raw_chunks)
            if new_ctx_rep.safe_chunks:
                re_gen = self.generator.generate(
                    reformulated_q,
                    new_ctx_rep.safe_chunks,
                    system_prompt=(
                        "You are SENTINEL. Strictly restrict your answer to the facts provided below. "
                        "State 'I do not have sufficient information' if not directly mentioned."
                    )
                )
                re_trust = self.trust_scorer.evaluate(query_text, re_gen.answer, new_ctx_rep.safe_chunks)
                if re_trust.trust_score > trust_rep.trust_score:
                    candidate_answer = re_gen.answer
                    trust_rep = re_trust
                    safe_chunks = new_ctx_rep.safe_chunks
                    context_report = new_ctx_rep

        # Check if trust recommendation mandates abstention
        is_abstained = False
        abstention_reason = None
        if trust_rep.recommendation == "ABSTAIN":
            is_abstained = True
            abstention_reason = trust_rep.verdict
            if trust_rep.verdict == "CONTRADICTED":
                abstain_obj = AbstentionEngine.direct_contradiction("Generated statement", "Context chunks")
            else:
                abstain_obj = AbstentionEngine.insufficient_evidence(query_text, trust_rep.retrieval_confidence)
            candidate_answer = abstain_obj.user_message

        # =====================================================================
        # BARRIER 6: Output & Egress Security Scanner
        # =====================================================================
        t0 = time.perf_counter()
        egress_res = self.egress_scanner.scan(candidate_answer, self.generator.system_prompt)
        t_egress = (time.perf_counter() - t0) * 1000
        final_answer = egress_res.sanitized_text

        total_t = (time.perf_counter() - start_time) * 1000

        return SentinelPipelineResult(
            query=query_text,
            answer=final_answer,
            is_abstained=is_abstained,
            abstention_reason=abstention_reason,
            trust_score=trust_rep.trust_score,
            trust_verdict=trust_rep.verdict,
            security_action=sec_verdict.action,
            retrieved_chunks=safe_chunks,
            quarantined_chunks_count=len(context_report.quarantined_chunks),
            security_verdict=sec_verdict,
            context_security=context_report,
            trust_report=trust_rep,
            egress_verdict=egress_res,
            telemetry=PipelineTelemetry(
                total_latency_ms=round(total_t, 2),
                input_scan_latency_ms=round(t_input, 2),
                retrieval_latency_ms=round(t_retrieval, 2),
                context_scan_latency_ms=round(t_ctx_scan, 2),
                generation_latency_ms=round(t_gen, 2),
                trust_eval_latency_ms=round(t_trust, 2),
                egress_scan_latency_ms=round(t_egress, 2),
                mitigation_triggered=mitigation_used
            )
        )

