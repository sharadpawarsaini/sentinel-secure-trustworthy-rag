"""Unit tests for Claim Extractor and NLI Verifier (Component 4.2 & 4.3).

Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

import pytest
from sentinel.rag.vector_store import RetrievedChunk
from sentinel.trust.claim_extractor import ClaimExtractor
from sentinel.trust.nli_verifier import NLIVerifier


def test_claim_extractor_splits_sentences():
    answer = (
        "Employees receive 25 days of paid annual vacation leave. "
        "Unused leave carries over up to a maximum threshold of 10 working days. "
        "Audit logs are retained in cold storage for 7 years."
    )
    claims = ClaimExtractor.extract_claims(answer)
    assert len(claims) == 3
    assert "Employees receive 25 days" in claims[0]
    assert "Unused leave carries over" in claims[1]
    assert "Audit logs are retained" in claims[2]


def test_claim_extractor_handles_bullets_and_fluff():
    answer = (
        "Based on the provided context, here is the answer:\n"
        "- The CEO of the company is John Smith.\n"
        "- He oversees global engineering."
    )
    claims = ClaimExtractor.extract_claims(answer)
    assert len(claims) == 2
    assert "The CEO of the company is John Smith" in claims[0]


def test_nli_verifier_entailment():
    verifier = NLIVerifier(use_mock=True)
    chunk = RetrievedChunk(
        chunk_id="chunk_1",
        text="Permanent employees are allocated 25 days of annual paid vacation leave.",
        source_filename="handbook.txt",
        chunk_index=0,
        similarity_score=0.90,
        distance=0.10,
        metadata={}
    )
    claim = "Employees receive 25 days of annual paid vacation leave."
    result = verifier.verify_claim(claim, [chunk])
    assert result.verdict == "ENTAILED"
    assert result.entailment_prob >= 0.50
    assert result.best_supporting_source == "handbook.txt"


def test_nli_verifier_contradiction():
    verifier = NLIVerifier(use_mock=True)
    chunk = RetrievedChunk(
        chunk_id="chunk_1",
        text="Audit logs are retained in encrypted cold storage for a statutory minimum of 7 years.",
        source_filename="handbook.txt",
        chunk_index=0,
        similarity_score=0.85,
        distance=0.15,
        metadata={}
    )
    # Contradictory claim: says logs are NOT retained or retained for 0 years
    contradictory_claim = "Audit logs are not retained in storage."
    result = verifier.verify_claim(contradictory_claim, [chunk])
    assert result.verdict == "CONTRADICTED"
    assert result.contradiction_prob >= 0.50

