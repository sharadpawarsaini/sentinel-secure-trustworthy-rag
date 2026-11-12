"""Composite Trust Score Engine and Decision Gate for SENTINEL.

Combines retrieval confidence, NLI claim entailment, and semantic relevance
into a mathematically justified Composite Trust Score.
Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.rag.vector_store import RetrievedChunk
from sentinel.trust.claim_extractor import ClaimExtractor
from sentinel.trust.confidence_scorer import RetrievalConfidenceScorer, RetrievalConfidenceReport
from sentinel.trust.nli_verifier import NLIVerifier, NLIReport


class TrustReport(BaseModel):
    """Complete evaluation report detailing answer trustworthiness."""
    trust_score: float = Field(..., description="Unified composite trust score in [0.0, 1.0].")
    verdict: Literal[
        "TRUSTWORTHY",
        "PARTIALLY_SUPPORTED",
        "INSUFFICIENTLY_SUPPORTED",
        "CONTRADICTED",
        "POTENTIALLY_HALLUCINATED"
    ] = Field(..., description="Actionable trust classification.")
    retrieval_confidence: float = Field(..., description="Score from retrieval confidence.")
    faithfulness_ratio: float = Field(..., description="Score from NLI claim verification.")
    semantic_relevance: float = Field(..., description="Top chunk cosine similarity.")
    claims_count: int
    entailed_claims: int
    contradicted_claims: int
    nli_report: NLIReport
    retrieval_report: RetrievalConfidenceReport
    recommendation: Literal["DELIVER", "WARN", "MITIGATE", "ABSTAIN"]
    explanation: str


class CompositeTrustScorer:
    """Evaluates composite trust using weighted multi-metric fusion."""

    def __init__(
        self,
        weight_retrieval: float = 0.25,
        weight_nli: float = 0.55,
        weight_relevance: float = 0.20,
        trust_high_threshold: Optional[float] = None,
        trust_low_threshold: Optional[float] = None,
        nli_verifier: Optional[NLIVerifier] = None
    ):
        """Initialize composite trust evaluator.

        Args:
            weight_retrieval: Weight w1 for retrieval confidence.
            weight_nli: Weight w2 for NLI claim faithfulness.
            weight_relevance: Weight w3 for semantic relevance.
            trust_high_threshold: Threshold for TRUSTWORTHY (default: settings.trust_threshold_high).
            trust_low_threshold: Threshold for PARTIALLY_SUPPORTED (default: settings.trust_threshold_low).
        """
        assert abs((weight_retrieval + weight_nli + weight_relevance) - 1.0) < 1e-4, "Weights must sum to 1.0"
        self.w1 = weight_retrieval
        self.w2 = weight_nli
        self.w3 = weight_relevance

        self.tau_high = trust_high_threshold or settings.trust_threshold_high
        self.tau_low = trust_low_threshold or settings.trust_threshold_low

        self.confidence_scorer = RetrievalConfidenceScorer()
        self.nli_verifier = nli_verifier or NLIVerifier()

    def evaluate(
        self,
        query: str,
        answer: str,
        chunks: List[RetrievedChunk]
    ) -> TrustReport:
        """Run complete trust evaluation pipeline on query, answer, and retrieved chunks."""
        # 1. Retrieval confidence evaluation
        retrieval_rep = self.confidence_scorer.compute_confidence(chunks)
        c_ret = retrieval_rep.confidence_score
        r_sem = retrieval_rep.top_similarity

        # 2. Extract atomic claims from answer
        claims = ClaimExtractor.extract_claims(answer)

        # 3. Verify claims using NLI
        nli_rep = self.nli_verifier.verify_answer(claims, chunks)
        f_nli = nli_rep.overall_faithfulness_ratio

        # Special case: Clean explicit abstention
        if "i do not have sufficient information" in answer.lower():
            return TrustReport(
                trust_score=1.0,
                verdict="TRUSTWORTHY",
                retrieval_confidence=c_ret,
                faithfulness_ratio=1.0,
                semantic_relevance=r_sem,
                claims_count=len(claims),
                entailed_claims=len(claims),
                contradicted_claims=0,
                nli_report=nli_rep,
                retrieval_report=retrieval_rep,
                recommendation="DELIVER",
                explanation="Model correctly recognized lack of context and generated an honest, verified abstention."
            )

        # 4. Compute composite trust score
        raw_trust = (self.w1 * c_ret) + (self.w2 * f_nli) + (self.w3 * r_sem)
        trust_score = round(max(0.0, min(1.0, raw_trust)), 4)

        # 5. Determine verdict & recommendation
        if nli_rep.has_critical_contradiction:
            verdict = "CONTRADICTED"
            trust_score = min(trust_score, 0.20)
            recommendation = "ABSTAIN"
            explanation = "One or more generated claims directly contradict the retrieved source evidence."
        elif len(claims) > 0 and f_nli < 0.35:
            verdict = "POTENTIALLY_HALLUCINATED"
            recommendation = "MITIGATE"
            explanation = "Most claims lack factual entailment in retrieved context, indicating potential hallucination."
        elif trust_score >= self.tau_high:
            verdict = "TRUSTWORTHY"
            recommendation = "DELIVER"
            explanation = "Generated answer is strongly grounded and mathematically entailed by retrieved documents."
        elif trust_score >= self.tau_low:
            verdict = "PARTIALLY_SUPPORTED"
            recommendation = "WARN"
            explanation = "Answer is partially supported by context, but contains ungrounded claims or weak retrieval evidence."
        else:
            verdict = "INSUFFICIENTLY_SUPPORTED"
            recommendation = "ABSTAIN"
            explanation = "Retrieval confidence and factual entailment are insufficient to verify this answer."

        return TrustReport(
            trust_score=trust_score,
            verdict=verdict,
            retrieval_confidence=c_ret,
            faithfulness_ratio=f_nli,
            semantic_relevance=r_sem,
            claims_count=len(claims),
            entailed_claims=nli_rep.entailed_claims_count,
            contradicted_claims=nli_rep.contradicted_claims_count,
            nli_report=nli_rep,
            retrieval_report=retrieval_rep,
            recommendation=recommendation,
            explanation=explanation
        )

