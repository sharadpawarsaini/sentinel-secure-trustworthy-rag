"""Unit tests for Retrieval Confidence and Composite Trust Scorer (Component 4.1 & 4.4).

Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

import pytest
from sentinel.rag.vector_store import RetrievedChunk
from sentinel.trust.confidence_scorer import RetrievalConfidenceScorer
from sentinel.trust.nli_verifier import NLIVerifier
from sentinel.trust.composite_scorer import CompositeTrustScorer


def test_retrieval_confidence_exponential_decay():
    scorer = RetrievalConfidenceScorer(decay_lambda=0.30)
    chunks = [
        RetrievedChunk(
            chunk_id="c1", text="text 1", source_filename="f1.txt", chunk_index=0,
            similarity_score=0.90, distance=0.10, metadata={}
        ),
        RetrievedChunk(
            chunk_id="c2", text="text 2", source_filename="f1.txt", chunk_index=1,
            similarity_score=0.70, distance=0.30, metadata={}
        ),
        RetrievedChunk(
            chunk_id="c3", text="text 3", source_filename="f1.txt", chunk_index=2,
            similarity_score=0.50, distance=0.50, metadata={}
        )
    ]
    rep = scorer.compute_confidence(chunks)
    assert 0.70 <= rep.confidence_score <= 0.90
    assert rep.top_similarity == 0.90
    assert rep.is_sufficient is True


def test_composite_trust_scorer_trustworthy():
    scorer = CompositeTrustScorer(nli_verifier=NLIVerifier(use_mock=True))
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            text="Permanent employees are allocated 25 days of annual paid vacation leave.",
            source_filename="handbook.txt",
            chunk_index=0,
            similarity_score=0.92,
            distance=0.08,
            metadata={}
        )
    ]
    query = "How many days of paid vacation do employees receive?"
    answer = "Employees receive 25 days of annual paid vacation leave."

    report = scorer.evaluate(query, answer, chunks)
    assert report.trust_score >= 0.75
    assert report.verdict == "TRUSTWORTHY"
    assert report.recommendation == "DELIVER"
    assert report.contradicted_claims == 0


def test_composite_trust_scorer_detects_contradiction():
    scorer = CompositeTrustScorer(nli_verifier=NLIVerifier(use_mock=True))
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            text="Audit logs are retained in encrypted cold storage for 7 years.",
            source_filename="handbook.txt",
            chunk_index=0,
            similarity_score=0.85,
            distance=0.15,
            metadata={}
        )
    ]
    query = "Are audit logs retained?"
    contradictory_answer = "Audit logs are not retained in storage."

    report = scorer.evaluate(query, contradictory_answer, chunks)
    assert report.verdict == "CONTRADICTED"
    assert report.trust_score <= 0.20
    assert report.recommendation == "ABSTAIN"

