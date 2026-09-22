"""Unit tests for VectorStoreManager (Component 2.5)."""

import pytest
from pathlib import Path
from sentinel.rag.chunker import TextChunk
from sentinel.rag.embedder import get_embedding_engine
from sentinel.rag.vector_store import VectorStoreManager, RetrievedChunk


@pytest.fixture
def temp_vector_store(tmp_path: Path):
    """Fixture providing an isolated temporary VectorStoreManager."""
    manager = VectorStoreManager(
        persist_dir=tmp_path / "chroma_test_db",
        collection_name="test_collection",
        embedder=get_embedding_engine()
    )
    yield manager
    # Teardown
    manager.clear_collection()


def test_add_and_query_chunks(temp_vector_store: VectorStoreManager):
    chunks = [
        TextChunk(
            chunk_id="chunk_ceo_001",
            text="The CEO and co-founder of the organization is John Smith.",
            source_filename="executive_bios.txt",
            chunk_index=0,
            start_char=0,
            end_char=58,
            character_count=58,
            metadata={"department": "Leadership"}
        ),
        TextChunk(
            chunk_id="chunk_prod_002",
            text="Our primary software product is an autonomous enterprise cybersecurity platform.",
            source_filename="product_overview.txt",
            chunk_index=0,
            start_char=0,
            end_char=80,
            character_count=80,
            metadata={"department": "Engineering"}
        ),
        TextChunk(
            chunk_id="chunk_hr_003",
            text="Employees receive 25 days of annual paid vacation leave.",
            source_filename="hr_policies.txt",
            chunk_index=0,
            start_char=0,
            end_char=56,
            character_count=56,
            metadata={"department": "Human Resources"}
        )
    ]

    added = temp_vector_store.add_chunks(chunks)
    assert added == 3

    # Query specifically for CEO
    results = temp_vector_store.query_similar("Who is the chief executive officer?", top_k=2)
    assert len(results) <= 2
    assert len(results) > 0

    top_chunk = results[0]
    assert isinstance(top_chunk, RetrievedChunk)
    assert top_chunk.chunk_id == "chunk_ceo_001"
    assert "John Smith" in top_chunk.text
    assert top_chunk.similarity_score > 0.50
    assert top_chunk.source_filename == "executive_bios.txt"


def test_score_threshold_filtering(temp_vector_store: VectorStoreManager):
    chunks = [
        TextChunk(
            chunk_id="c1",
            text="Quantum computing utilizes qubits for matrix superposition.",
            source_filename="quantum.txt",
            chunk_index=0,
            start_char=0,
            end_char=60,
            character_count=60
        )
    ]
    temp_vector_store.add_chunks(chunks)

    # Completely unrelated query with high threshold should yield 0 results
    results = temp_vector_store.query_similar(
        query_text="How to bake homemade Italian pizza dough?",
        top_k=2,
        score_threshold=0.85
    )
    assert len(results) == 0


def test_collection_stats_and_delete(temp_vector_store: VectorStoreManager):
    chunks = [
        TextChunk(
            chunk_id="doc1_chunk0",
            text="Policy on data encryption standards.",
            source_filename="sec_policy.txt",
            chunk_index=0,
            start_char=0,
            end_char=37,
            character_count=37
        ),
        TextChunk(
            chunk_id="doc2_chunk0",
            text="Office location and address in San Francisco.",
            source_filename="locations.txt",
            chunk_index=0,
            start_char=0,
            end_char=45,
            character_count=45
        )
    ]
    temp_vector_store.add_chunks(chunks)

    stats = temp_vector_store.get_collection_stats()
    assert stats["total_chunks"] == 2
    assert stats["unique_documents_count"] == 2
    assert "sec_policy.txt" in stats["unique_documents"]

    # Delete one document
    deleted = temp_vector_store.delete_document("sec_policy.txt")
    assert deleted == 1

    updated_stats = temp_vector_store.get_collection_stats()
    assert updated_stats["total_chunks"] == 1
    assert "sec_policy.txt" not in updated_stats["unique_documents"]
