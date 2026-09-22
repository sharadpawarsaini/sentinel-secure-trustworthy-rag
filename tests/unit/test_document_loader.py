"""Unit tests for DocumentLoader (Component 2.2)."""

import pytest
from pathlib import Path
from sentinel.rag.document_loader import DocumentLoader, LoadedDocument


def test_load_txt_from_bytes():
    sample_text = "SENTINEL: Secure and Trustworthy RAG System.\nLine 2: Grounded retrieval."
    raw_bytes = sample_text.encode("utf-8")
    
    doc = DocumentLoader.load_from_bytes(raw_bytes, "sample.txt")
    
    assert isinstance(doc, LoadedDocument)
    assert doc.source_filename == "sample.txt"
    assert doc.file_type == ".txt"
    assert "Grounded retrieval." in doc.text
    assert doc.character_count == len(doc.text)
    assert doc.page_count == 1


def test_load_txt_file(tmp_path: Path):
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("Company CEO is John Smith.\nFounded in 2015.", encoding="utf-8")
    
    doc = DocumentLoader.load(test_file)
    
    assert doc.source_filename == "test_doc.txt"
    assert "John Smith" in doc.text
    assert doc.character_count > 0


def test_unsupported_file_extension():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        DocumentLoader.load_from_bytes(b"some content", "file.exe")


def test_empty_file():
    with pytest.raises(ValueError, match="is empty"):
        DocumentLoader.load_from_bytes(b"", "empty.txt")


def test_whitespace_normalization():
    dirty_text = "Line 1\r\nLine 2\r\n\xa0Indented text\x00"
    raw_bytes = dirty_text.encode("utf-8")
    
    doc = DocumentLoader.load_from_bytes(raw_bytes, "dirty.txt")
    assert "\r" not in doc.text
    assert "\x00" not in doc.text
    assert "Indented text" in doc.text
