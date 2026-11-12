"""Transparent Abstention and Explanatory Response Engine for SENTINEL.

Generates structured, explainable abstention verdicts when trust cannot be guaranteed.
Owned by: Sharad (System Architect & Integration Engineer)
"""

from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field


class AbstentionResult(BaseModel):
    """Structured transparent response delivered when SENTINEL abstains from answering."""
    abstain: bool = True
    reason_code: Literal[
        "SECURITY_BLOCK",
        "INSUFFICIENT_EVIDENCE",
        "DIRECT_CONTRADICTION",
        "POTENTIAL_HALLUCINATION",
        "CONTEXT_QUARANTINED"
    ]
    user_message: str
    technical_explanation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AbstentionEngine:
    """Generates standardized, honest, and explainable abstention responses."""

    @classmethod
    def security_block(cls, details: Optional[Dict[str, Any]] = None) -> AbstentionResult:
        """Abstention due to input prompt injection or policy breach."""
        return AbstentionResult(
            abstain=True,
            reason_code="SECURITY_BLOCK",
            user_message=(
                "I cannot process this request because it violates system security guidelines "
                "or contains prompt injection patterns."
            ),
            technical_explanation="Input scanner flagged direct injection or delimiter hijacking signatures.",
            metadata=details or {}
        )

    @classmethod
    def insufficient_evidence(cls, query: str, confidence: float) -> AbstentionResult:
        """Abstention due to retrieval failure or lack of documentation."""
        return AbstentionResult(
            abstain=True,
            reason_code="INSUFFICIENT_EVIDENCE",
            user_message=(
                "I do not have sufficient information in the verified knowledge base to answer this question accurately."
            ),
            technical_explanation=f"Retrieval confidence score ({confidence:.2f}) was below the reliability threshold.",
            metadata={"query": query, "retrieval_confidence": confidence}
        )

    @classmethod
    def direct_contradiction(cls, violated_claim: str, source_evidence: Optional[str]) -> AbstentionResult:
        """Abstention due to contradiction with ground truth context."""
        return AbstentionResult(
            abstain=True,
            reason_code="DIRECT_CONTRADICTION",
            user_message=(
                "I cannot present this answer because the generated statement directly contradicts "
                "the verified source documents in the knowledge base."
            ),
            technical_explanation=f"Claim '{violated_claim}' contradicted verified evidence.",
            metadata={"violated_claim": violated_claim, "source": source_evidence}
        )

    @classmethod
    def potential_hallucination(cls, faithfulness: float) -> AbstentionResult:
        """Abstention due to high hallucination risk."""
        return AbstentionResult(
            abstain=True,
            reason_code="POTENTIAL_HALLUCINATION",
            user_message=(
                "I am withholding this answer because it cannot be reliably grounded in the provided documents."
            ),
            technical_explanation=f"NLI claim faithfulness ratio ({faithfulness:.2f}) indicates unsupported claims.",
            metadata={"faithfulness_ratio": faithfulness}
        )

