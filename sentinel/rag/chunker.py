"""Deterministic text chunker for SENTINEL.

Splits extracted document text into semantic chunks with configurable size,
overlap, and deterministic SHA-256 chunk identifiers.
Owned by: Bhumika (RAG Foundation)
"""

import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sentinel.rag.document_loader import LoadedDocument


class TextChunk(BaseModel):
    """Structured representation of an individual text chunk."""
    chunk_id: str = Field(..., description="Deterministic SHA-256 hash identifying the chunk.")
    text: str = Field(..., description="Text content of this chunk.")
    source_filename: str = Field(..., description="Source document filename.")
    chunk_index: int = Field(..., description="0-indexed position within the document.")
    start_char: int = Field(..., description="Start character offset in the parent document.")
    end_char: int = Field(..., description="End character offset in the parent document.")
    character_count: int = Field(..., description="Length of chunk text.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parent and chunk metadata.")


class TextChunker:
    """Recursive character chunker with deterministic ID generation."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """Initialize the chunker.

        Args:
            chunk_size: Maximum target character length per chunk.
            chunk_overlap: Number of overlapping characters between consecutive chunks.
            separators: Hierarchical delimiters to try, in priority order.
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    @staticmethod
    def generate_chunk_id(source_filename: str, chunk_index: int, text: str) -> str:
        """Generate a deterministic SHA-256 chunk identifier.

        Args:
            source_filename: Name of the originating document.
            chunk_index: Sequential index.
            text: Text content of the chunk.

        Returns:
            Hex digest string (first 16 characters for concise, collision-safe IDs).
        """
        payload = f"{source_filename}::{chunk_index}::{text.strip()}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    def chunk_document(self, doc: LoadedDocument) -> List[TextChunk]:
        """Split a LoadedDocument into a list of TextChunks.

        Args:
            doc: LoadedDocument instance from DocumentLoader.

        Returns:
            List of TextChunk instances.
        """
        return self.chunk_text(
            text=doc.text,
            source_filename=doc.source_filename,
            parent_metadata=doc.metadata
        )

    def chunk_text(
        self,
        text: str,
        source_filename: str = "raw_input",
        parent_metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """Split raw text into TextChunks.

        Args:
            text: Raw string to chunk.
            source_filename: Filename for attribution and hashing.
            parent_metadata: Metadata inherited from document.

        Returns:
            List of TextChunks.
        """
        text = text.strip()
        if not text:
            return []

        # If text is smaller than or equal to chunk_size, return single chunk
        if len(text) <= self.chunk_size:
            chunk_id = self.generate_chunk_id(source_filename, 0, text)
            meta = dict(parent_metadata or {})
            return [
                TextChunk(
                    chunk_id=chunk_id,
                    text=text,
                    source_filename=source_filename,
                    chunk_index=0,
                    start_char=0,
                    end_char=len(text),
                    character_count=len(text),
                    metadata=meta
                )
            ]

        raw_splits = self._recursive_split(text, self.separators)
        merged_chunks = self._merge_splits(raw_splits, text)

        chunks: List[TextChunk] = []
        for idx, (chunk_text, start_char, end_char) in enumerate(merged_chunks):
            chunk_id = self.generate_chunk_id(source_filename, idx, chunk_text)
            meta = dict(parent_metadata or {})
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    source_filename=source_filename,
                    chunk_index=idx,
                    start_char=start_char,
                    end_char=end_char,
                    character_count=len(chunk_text),
                    metadata=meta
                )
            )

        return chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Hierarchically split text using the best matching separator."""
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator != "" else list(text)

        good_splits: List[str] = []
        for s in splits:
            if separator != "" and s != splits[-1]:
                piece = s + separator
            else:
                piece = s

            if not piece:
                continue

            if len(piece) <= self.chunk_size:
                good_splits.append(piece)
            else:
                if new_separators:
                    other_splits = self._recursive_split(piece, new_separators)
                    good_splits.extend(other_splits)
                else:
                    good_splits.append(piece)

        return good_splits

    def _merge_splits(
        self,
        splits: List[str],
        original_text: str
    ) -> List[tuple[str, int, int]]:
        """Combine smaller splits up to chunk_size respecting chunk_overlap."""
        merged: List[tuple[str, int, int]] = []
        current_doc: List[str] = []
        total_len = 0
        search_start = 0

        for piece in splits:
            piece_len = len(piece)
            if total_len + piece_len > self.chunk_size and current_doc:
                chunk_str = "".join(current_doc).strip()
                if chunk_str:
                    # Find offset in original text
                    start_pos = original_text.find(chunk_str, search_start)
                    if start_pos == -1:
                        start_pos = max(0, search_start)
                    end_pos = start_pos + len(chunk_str)
                    merged.append((chunk_str, start_pos, end_pos))
                    search_start = max(0, end_pos - self.chunk_overlap)

                # Keep overlap pieces
                while total_len > self.chunk_overlap and current_doc:
                    popped = current_doc.pop(0)
                    total_len -= len(popped)

            current_doc.append(piece)
            total_len += piece_len

        if current_doc:
            chunk_str = "".join(current_doc).strip()
            if chunk_str:
                start_pos = original_text.find(chunk_str, search_start)
                if start_pos == -1:
                    start_pos = max(0, search_start)
                end_pos = start_pos + len(chunk_str)
                merged.append((chunk_str, start_pos, end_pos))

        return merged
