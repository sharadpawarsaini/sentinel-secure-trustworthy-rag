"""Retrieved-Context Security Barrier and Indirect Prompt Injection Filter for SENTINEL.

Validates top-K retrieved chunks before passing to the LLM generator.
Evicts poisoned, untrusted, or hijacked chunks from generation context.
Owned by: Adhya (AI Security Engineer)
"""

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

from sentinel.rag.vector_store import RetrievedChunk
from sentinel.security.input_scanner import InputScanner
from sentinel.security.document_scanner import DocumentScanner


class ContextSecurityReport(BaseModel):
    """Report detailing retrieved chunk filtering and quarantine status."""
    total_retrieved: int
    safe_chunks: List[RetrievedChunk] = Field(default_factory=list)
    quarantined_chunks: List[RetrievedChunk] = Field(default_factory=list)
    eviction_reasons: Dict[str, str] = Field(default_factory=dict)
    all_chunks_safe: bool = True


class ContextScanner:
    """Intermediary security barrier between Vector Retrieval and LLM Generation."""

    def __init__(self):
        self.input_scanner = InputScanner()
        self.doc_scanner = DocumentScanner()

    def filter_retrieved_context(
        self,
        chunks: List[RetrievedChunk]
    ) -> ContextSecurityReport:
        """Filter out any retrieved chunks containing indirect prompt injections.
        
        Args:
            chunks: List of RetrievedChunk objects from VectorStoreManager.

        Returns:
            ContextSecurityReport containing safe chunks and quarantined chunks with reasons.
        """
        if not chunks:
            return ContextSecurityReport(
                total_retrieved=0,
                safe_chunks=[],
                quarantined_chunks=[],
                eviction_reasons={},
                all_chunks_safe=True
            )

        safe_chunks: List[RetrievedChunk] = []
        quarantined_chunks: List[RetrievedChunk] = []
        eviction_reasons: Dict[str, str] = {}

        for chunk in chunks:
            # Check 1: Was chunk pre-flagged as quarantined in vectorstore metadata?
            if chunk.metadata.get("is_quarantined") is True or chunk.metadata.get("is_quarantined") == "True":
                quarantined_chunks.append(chunk)
                eviction_reasons[chunk.chunk_id] = str(chunk.metadata.get("quarantine_reason", "Pre-quarantined chunk"))
                continue

            # Check 2: Dynamic input scan for indirect prompt injection tags
            verdict = self.input_scanner.scan(chunk.text)
            if verdict.is_malicious or verdict.action == "BLOCK":
                quarantined_chunks.append(chunk)
                eviction_reasons[chunk.chunk_id] = f"Indirect injection detected: {'; '.join(verdict.matched_patterns)}"
                continue

            # Check 3: Check for embedded poison commands
            # (e.g. instructions disguised as notes or comments)
            norm_text = chunk.text.lower()
            if any(marker in norm_text for marker in [
                "ignore previous", "disregard the above", "system prompt:",
                "[instruction:", "do anything now", "<|im_start|>"
            ]):
                quarantined_chunks.append(chunk)
                eviction_reasons[chunk.chunk_id] = "Suspicious indirect override substring matched"
                continue

            # If all checks pass, chunk is deemed safe
            safe_chunks.append(chunk)

        all_safe = len(quarantined_chunks) == 0

        return ContextSecurityReport(
            total_retrieved=len(chunks),
            safe_chunks=safe_chunks,
            quarantined_chunks=quarantined_chunks,
            eviction_reasons=eviction_reasons,
            all_chunks_safe=all_safe
        )

