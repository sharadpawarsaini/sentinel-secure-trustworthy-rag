"""Unit tests for EmbeddingEngine (Component 2.4)."""

import pytest
from sentinel.rag.embedder import EmbeddingEngine, get_embedding_engine


@pytest.fixture(scope="module")
def embedder():
    """Shared EmbeddingEngine fixture."""
    return get_embedding_engine()


def test_embedding_dimension(embedder: EmbeddingEngine):
    dim = embedder.dimension
    assert dim == 384
    
    vec = embedder.embed_text("Test sentence for dimension verification.")
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)


def test_embedding_batch(embedder: EmbeddingEngine):
    sentences = [
        "First test document about RAG architecture.",
        "Second test document about prompt injection defense.",
        "Third document covering hallucination mitigation."
    ]
    vectors = embedder.embed_batch(sentences)
    
    assert len(vectors) == 3
    for vec in vectors:
        assert len(vec) == 384


def test_semantic_similarity_ranking(embedder: EmbeddingEngine):
    query_vec = embedder.embed_text("artificial intelligence and machine learning models")
    tech_vec = embedder.embed_text("deep neural networks, transformers, and supervised learning")
    food_vec = embedder.embed_text("how to prepare chocolate chip cookies with organic butter")
    
    sim_tech = embedder.cosine_similarity(query_vec, tech_vec)
    sim_food = embedder.cosine_similarity(query_vec, food_vec)
    
    # AI query must be significantly more similar to neural networks than to baking cookies
    assert sim_tech > sim_food
    assert sim_tech > 0.50
    assert sim_food < 0.40


def test_empty_batch(embedder: EmbeddingEngine):
    assert embedder.embed_batch([]) == []
