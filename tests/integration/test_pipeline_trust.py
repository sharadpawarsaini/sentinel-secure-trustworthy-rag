"""Integration tests for SENTINEL Pipeline Trust & Abstention Engine (Phase 4 Integration).

Tests closed-loop trust scoring, claim grounding, contradiction handling, and honest abstention.
Owned by: Sharad (System Architect & Integration Engineer)
"""

from pathlib import Path
import pytest

from sentinel.rag.document_loader import DocumentLoader
from sentinel.rag.chunker import TextChunker
from sentinel.rag.embedder import get_embedding_engine
from sentinel.rag.vector_store import VectorStoreManager
from sentinel.rag.generator import BaselineGenerator, MockLLMClient
from sentinel.trust.composite_scorer import CompositeTrustScorer
from sentinel.trust.nli_verifier import NLIVerifier
from sentinel.pipeline import SentinelPipeline


@pytest.fixture
def trust_pipeline(tmp_path: Path):
    """Instantiate an isolated SentinelPipeline for trust integration testing."""
    embedder = get_embedding_engine()
    store = VectorStoreManager(
        persist_dir=tmp_path / "trust_test_chroma",
        collection_name="trust_test_col",
        embedder=embedder
    )
    mock_llm = MockLLMClient()
    generator = BaselineGenerator(llm_client=mock_llm)
    trust_scorer = CompositeTrustScorer(nli_verifier=NLIVerifier(use_mock=True))

    pipe = SentinelPipeline(
        vector_store=store,
        generator=generator,
        trust_scorer=trust_scorer
    )

    yield pipe
    store.clear_collection()


def test_pipeline_trustworthy_answer_on_grounded_evidence(trust_pipeline):
    store = trust_pipeline.vector_store
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)

    doc_text = "The Chief Executive Officer (CEO) of the technology corporation is John Smith."
    doc = DocumentLoader.load_from_bytes(doc_text.encode("utf-8"), filename="company.txt")
    chunks = chunker.chunk_document(doc)
    store.add_chunks(chunks)

    res = trust_pipeline.query("Who is the CEO of the technology corporation?")

    assert res.is_abstained is False
    assert res.trust_score >= 0.70
    assert res.trust_verdict == "TRUSTWORTHY"
    assert len(res.retrieved_chunks) >= 1
    assert "John Smith" in res.retrieved_chunks[0].text


def test_pipeline_abstains_when_no_context_exists(trust_pipeline):
    # Empty store
    res = trust_pipeline.query("What is the company policy on space travel?")

    assert res.is_abstained is True
    assert res.abstention_reason == "INSUFFICIENT_EVIDENCE"
    assert "sufficient information" in res.answer.lower()

