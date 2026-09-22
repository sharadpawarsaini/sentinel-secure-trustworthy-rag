"""Unit tests for BaselineGenerator (Component 2.6)."""

import pytest
from sentinel.rag.generator import BaselineGenerator, MockLLMClient, GenerationResult
from sentinel.rag.vector_store import RetrievedChunk


@pytest.fixture
def mock_generator():
    """Generator configured with deterministic MockLLMClient."""
    client = MockLLMClient(model_name="mock-llama3")
    return BaselineGenerator(llm_client=client)


def test_format_context_multiple_chunks(mock_generator: BaselineGenerator):
    chunks = [
        RetrievedChunk(
            chunk_id="chk1",
            text="First fact: Company founded in 2015.",
            source_filename="about.txt",
            chunk_index=0,
            similarity_score=0.88,
            distance=0.12
        ),
        RetrievedChunk(
            chunk_id="chk2",
            text="Second fact: Headquartered in New York.",
            source_filename="about.txt",
            chunk_index=1,
            similarity_score=0.82,
            distance=0.18
        )
    ]
    formatted = mock_generator.format_context(chunks)
    assert "[Source 1: about.txt, Chunk 0 | Sim: 0.88]" in formatted
    assert "[Source 2: about.txt, Chunk 1 | Sim: 0.82]" in formatted
    assert "Company founded in 2015" in formatted


def test_format_context_empty(mock_generator: BaselineGenerator):
    formatted = mock_generator.format_context([])
    assert "None (No relevant evidence retrieved)" in formatted


def test_generate_grounded_answer(mock_generator: BaselineGenerator):
    chunks = [
        RetrievedChunk(
            chunk_id="chk_ceo",
            text="The CEO of the enterprise is John Smith.",
            source_filename="leadership.txt",
            chunk_index=0,
            similarity_score=0.91,
            distance=0.09
        )
    ]
    res = mock_generator.generate(query="Who is the CEO?", chunks=chunks)
    
    assert isinstance(res, GenerationResult)
    assert "John Smith" in res.answer
    assert res.provider == "mock"
    assert res.model == "mock-llama3"
    assert res.latency_ms >= 0.0
    assert len(res.retrieved_chunks) == 1


def test_generate_insufficient_evidence(mock_generator: BaselineGenerator):
    res = mock_generator.generate(query="What is the net profit in 2021?", chunks=[])
    
    assert "sufficient information" in res.answer.lower()
    assert len(res.retrieved_chunks) == 0
