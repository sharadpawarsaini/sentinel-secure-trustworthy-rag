"""SENTINEL Trust Evaluation Package.

Provides NLI verification, claim extraction, retrieval confidence scoring,
and composite trust formulation.
Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

from sentinel.trust.claim_extractor import ClaimExtractor
from sentinel.trust.confidence_scorer import RetrievalConfidenceScorer, RetrievalConfidenceReport
from sentinel.trust.nli_verifier import NLIVerifier, ClaimNLIResult, NLIReport
from sentinel.trust.composite_scorer import CompositeTrustScorer, TrustReport

__all__ = [
    "ClaimExtractor",
    "RetrievalConfidenceScorer",
    "RetrievalConfidenceReport",
    "NLIVerifier",
    "ClaimNLIResult",
    "NLIReport",
    "CompositeTrustScorer",
    "TrustReport",
]

