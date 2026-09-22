"""Unit tests for TextChunker (Component 2.3)."""

import pytest
from sentinel.rag.chunker import TextChunker, TextChunk
from sentinel.rag.document_loader import LoadedDocument


def test_chunk_short_text():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "Short text under target size."
    
    chunks = chunker.chunk_text(text, source_filename="short.txt")
    
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)
    assert len(chunks[0].chunk_id) == 16


def test_chunk_long_text_and_overlap():
    chunker = TextChunker(chunk_size=150, chunk_overlap=30)
    
    paragraphs = [
        "Paragraph 1 discusses the fundamental mechanics of dense semantic retrieval.",
        "Paragraph 2 outlines how dual-encoders map queries and passages to dense vectors.",
        "Paragraph 3 introduces Approximate Nearest Neighbor indexing using HNSW graphs.",
        "Paragraph 4 explains the role of cross-encoder rerankers in fine-grained scoring."
    ]
    full_text = "\n\n".join(paragraphs)
    
    chunks = chunker.chunk_text(full_text, source_filename="retrieval_notes.txt")
    
    assert len(chunks) > 1
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.character_count <= 200  # allowing slight boundary slack
        assert len(chunk.chunk_id) == 16


def test_chunk_id_determinism():
    chunker = TextChunker(chunk_size=200, chunk_overlap=40)
    sample_text = "SENTINEL project requires reproducible, deterministic identifiers for all chunks."
    
    chunks1 = chunker.chunk_text(sample_text, source_filename="audit.txt")
    chunks2 = chunker.chunk_text(sample_text, source_filename="audit.txt")
    
    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id


def test_chunk_document_integration():
    doc = LoadedDocument(
        text="Section A: Security policy.\nSection B: Access control.\nSection C: Audit trails.",
        source_filename="policy.txt",
        file_type=".txt",
        character_count=77,
        page_count=1,
        metadata={"category": "compliance"}
    )
    
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.source_filename == "policy.txt"
        assert chunk.metadata.get("category") == "compliance"


def test_invalid_chunk_parameters():
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        TextChunker(chunk_size=0)
        
    with pytest.raises(ValueError, match="must be strictly less"):
        TextChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="must be strictly less"):
        TextChunker(chunk_size=100, chunk_overlap=150)
