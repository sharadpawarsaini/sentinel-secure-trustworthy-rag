"""Baseline RAG System A - End-to-End Control Verification Test (Component 2.8).

This test suite executes the complete unaugmented Baseline RAG pipeline
(Extract -> Chunk -> Embed -> Store -> Retrieve -> Generate) to verify that
System A functions as an immutable, reproducible control group for Phase 6 benchmarking.
"""

from pathlib import Path
import pytest

from sentinel.rag.document_loader import DocumentLoader
from sentinel.rag.chunker import TextChunker
from sentinel.rag.embedder import get_embedding_engine
from sentinel.rag.vector_store import VectorStoreManager
from sentinel.rag.generator import BaselineGenerator, MockLLMClient, GenerationResult


@pytest.fixture
def baseline_pipeline(tmp_path: Path):
    """Initializes an isolated baseline RAG pipeline."""
    embedder = get_embedding_engine()
    vector_store = VectorStoreManager(
        persist_dir=tmp_path / "control_group_chroma",
        collection_name="control_baseline_a",
        embedder=embedder
    )
    chunker = TextChunker(chunk_size=200, chunk_overlap=30)
    mock_llm = MockLLMClient(model_name="baseline-control-llama3")
    generator = BaselineGenerator(llm_client=mock_llm)

    yield {
        "loader": DocumentLoader,
        "chunker": chunker,
        "vector_store": vector_store,
        "generator": generator
    }

    # Teardown
    vector_store.clear_collection()


def test_baseline_system_a_complete_lifecycle(baseline_pipeline, tmp_path: Path):
    loader = baseline_pipeline["loader"]
    chunker = baseline_pipeline["chunker"]
    vector_store = baseline_pipeline["vector_store"]
    generator = baseline_pipeline["generator"]

    # 1. Create a canonical benchmark sample document
    sample_doc_content = (
        "SECTION 1: ORGANIZATIONAL GOVERNANCE\n"
        "The Chief Executive Officer (CEO) of the technology corporation is John Smith.\n"
        "He oversees global engineering, security architecture, and strategic development.\n\n"
        "SECTION 2: TIME OFF AND EMPLOYEE BENEFITS\n"
        "All permanent employees are allocated 25 days of annual paid vacation leave.\n"
        "Unused leave carries over up to a maximum threshold of 10 working days.\n\n"
        "SECTION 3: DATA RETENTION ARCHITECTURE\n"
        "Audit logs are retained in encrypted cold storage for a statutory minimum of 7 years."
    )
    doc_path = tmp_path / "company_handbook.txt"
    doc_path.write_text(sample_doc_content, encoding="utf-8")

    # 2. Extract Text & Metadata
    loaded_doc = loader.load(doc_path)
    assert loaded_doc.character_count == len(sample_doc_content)
    assert loaded_doc.source_filename == "company_handbook.txt"

    # 3. Chunk Document
    chunks = chunker.chunk_document(loaded_doc)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert chunk.source_filename == "company_handbook.txt"
        assert len(chunk.chunk_id) == 16

    # 4. Embed & Store into ChromaDB
    added = vector_store.add_chunks(chunks)
    assert added == len(chunks)

    stats = vector_store.get_collection_stats()
    assert stats["total_chunks"] == len(chunks)
    assert "company_handbook.txt" in stats["unique_documents"]

    # 5. Query 1: Fact Retrieval (CEO)
    ceo_chunks = vector_store.query_similar("Who is the company CEO?", top_k=2)
    assert len(ceo_chunks) > 0
    assert "John Smith" in ceo_chunks[0].text
    assert ceo_chunks[0].similarity_score > 0.40

    ceo_generation = generator.generate("Who is the company CEO?", chunks=ceo_chunks)
    assert isinstance(ceo_generation, GenerationResult)
    assert "John Smith" in ceo_generation.answer
    assert ceo_generation.provider == "mock"
    assert ceo_generation.latency_ms >= 0.0

    # 6. Query 2: Fact Retrieval (Vacation days)
    vacation_chunks = vector_store.query_similar("How many days of paid vacation leave do employees get?", top_k=2)
    assert len(vacation_chunks) > 0
    assert "25 days" in vacation_chunks[0].text

    vacation_gen = generator.generate("How many days of paid vacation leave do employees get?", chunks=vacation_chunks)
    assert "25 days" in vacation_gen.answer

    # 7. Query 3: Out-of-Corpus Query (Testing baseline hallucination / insufficient info surface)
    missing_chunks = vector_store.query_similar("What is the company stock ticker symbol?", top_k=2, score_threshold=0.85)
    missing_gen = generator.generate("What is the company stock ticker symbol?", chunks=missing_chunks)
    assert "sufficient information" in missing_gen.answer.lower()
