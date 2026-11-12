"""Retrieval Confidence and Context Relevance Scorer for SENTINEL.

Computes mathematically grounded retrieval confidence using exponential rank-decay
and cosine score dispersion across retrieved context chunks.
Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

import math
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from sentinel.rag.vector_store import RetrievedChunk


class RetrievalConfidenceReport(BaseModel):
    """Structured report of vector retrieval confidence metrics."""
    confidence_score: float = Field(..., description="Rank-decayed retrieval confidence in [0.0, 1.0].")
    top_similarity: float = Field(..., description="Cosine similarity score of top-1 chunk.")
    mean_similarity: float = Field(..., description="Average similarity across top-K chunks.")
    chunks_evaluated: int = Field(..., description="Number of valid chunks scored.")
    is_sufficient: bool = Field(..., description="True if confidence exceeds sufficiency threshold.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Detailed score metrics.")


class RetrievalConfidenceScorer:
    """Evaluates the semantic grounding strength of retrieved context chunks."""

    def __init__(
        self,
        decay_lambda: float = 0.30,
        sufficiency_threshold: float = 0.45
    ):
        """Initialize retrieval confidence calculator.

        Args:
            decay_lambda: Exponential rank discount rate (default: 0.30).
            sufficiency_threshold: Minimum confidence required for reliable grounding (default: 0.45).
        """
        self.decay_lambda = decay_lambda
        self.sufficiency_threshold = sufficiency_threshold

    def compute_confidence(self, chunks: List[RetrievedChunk]) -> RetrievalConfidenceReport:
        """Compute exponential rank-decay retrieval confidence score.
        
        Formula:
            w_i = exp(-lambda * (i - 1))
            C_ret = sum(max(0, s_i) * w_i) / sum(w_i)
        """
        if not chunks:
            return RetrievalConfidenceReport(
                confidence_score=0.0,
                top_similarity=0.0,
                mean_similarity=0.0,
                chunks_evaluated=0,
                is_sufficient=False,
                metadata={"reason": "No chunks retrieved"}
            )

        weights = []
        weighted_sum = 0.0
        scores = []

        for i, chunk in enumerate(chunks):
            # Rank index i starts at 0 for rank 1
            rank_weight = math.exp(-self.decay_lambda * i)
            sim_score = max(0.0, min(1.0, chunk.similarity_score))

            scores.append(sim_score)
            weights.append(rank_weight)
            weighted_sum += sim_score * rank_weight

        total_weight = sum(weights)
        confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        confidence = round(confidence, 4)

        top_sim = round(scores[0], 4) if scores else 0.0
        mean_sim = round(sum(scores) / len(scores), 4) if scores else 0.0
        is_sufficient = confidence >= self.sufficiency_threshold

        return RetrievalConfidenceReport(
            confidence_score=confidence,
            top_similarity=top_sim,
            mean_similarity=mean_sim,
            chunks_evaluated=len(chunks),
            is_sufficient=is_sufficient,
            metadata={
                "decay_lambda": self.decay_lambda,
                "scores_breakdown": scores,
                "sufficiency_threshold": self.sufficiency_threshold
            }
        )

