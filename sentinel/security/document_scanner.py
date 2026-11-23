"""Document Ingestion Poisoning and Adversarial Payload Scanner for SENTINEL.

Inspects document chunks during ingestion to detect indirect prompt injections,
canary override strings, and hidden exfiltration beacons.
Owned by: Adhya (AI Security Engineer)
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from sentinel.rag.chunker import TextChunk
from sentinel.security.normalizer import TextNormalizer


class DocumentChunkVerdict(BaseModel):
    """Security assessment for a single ingested document chunk."""
    chunk_id: str
    chunk_index: int
    is_poisoned: bool
    risk_score: float
    quarantine_reason: Optional[str] = None
    detected_patterns: List[str] = Field(default_factory=list)


class DocumentScanReport(BaseModel):
    """Aggregate report of document ingestion security audit."""
    source_filename: str
    total_chunks: int
    quarantined_chunks_count: int
    clean_chunks_count: int
    has_poisoned_content: bool
    verdicts: List[DocumentChunkVerdict] = Field(default_factory=list)


class DocumentScanner:
    """Detects adversarial poisoning attacks inside uploaded knowledge base documents."""

    # Document poisoning signatures: instructions embedded to manipulate downstream RAG sessions
    POISON_PATTERNS = [
        (re.compile(r"\[\s*(?:INSTRUCTION|SYSTEM\s+PROMPT|SYSTEM\s+OVERRIDE|OVERRIDE|ADMIN_COMMAND)\s*:\s*[^\]]+\]", re.I), "embedded_instruction_tag", 0.90),
        (re.compile(r"\b(?:NOTE\s+TO\s+(?:AI|LLM|ASSISTANT)|ATTENTION\s+ASSISTANT)\s*:\s*", re.I), "model_directed_note", 0.85),
        (re.compile(r"\bwhen\s+answering\s+(?:this|any)\s+query,\s+(?:ignore|forget|bypass)\b", re.I), "conditional_override_poison", 0.85),
        (re.compile(r"\bsecretly\s+(?:send|transmit|exfiltrate|forward|append)\s+(?:the\s+)?(?:data|token|context|password)\b", re.I), "exfiltration_instruction", 0.95),
        (re.compile(r"!\[(?:beacon|track|ping|exfil)\]\(https?://[^\)]+\)", re.I), "markdown_image_exfiltration_beacon", 0.90),
        (re.compile(r"\b(?:curl|wget|fetch|Invoke-WebRequest)\s+https?://[^\s]+", re.I), "command_injection_attempt", 0.85),
        (re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S), "html_script_injection", 0.95),
    ]

    def __init__(self, poison_threshold: float = 0.70):
        self.poison_threshold = poison_threshold

    def scan_chunk(self, chunk: TextChunk) -> DocumentChunkVerdict:
        """Scan a single TextChunk for poisoning signatures."""
        norm_res = TextNormalizer.normalize(chunk.text)
        scan_target = norm_res.normalized_text

        detected: List[str] = []
        risk_score = 0.0

        if norm_res.has_obfuscation:
            detected.append(f"chunk_obfuscation({','.join(norm_res.transformations_applied)})")
            risk_score += 0.35

        for pattern, tag, weight in self.POISON_PATTERNS:
            match = pattern.search(scan_target)
            if match:
                detected.append(f"{tag}:{match.group(0)[:60]}")
                risk_score += weight

        calibrated_risk = min(1.0, round(risk_score, 4))
        is_poisoned = calibrated_risk >= self.poison_threshold

        reason = None
        if is_poisoned:
            reason = f"Poisoning signatures detected: {'; '.join(detected)}"

        return DocumentChunkVerdict(
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
            is_poisoned=is_poisoned,
            risk_score=calibrated_risk,
            quarantine_reason=reason,
            detected_patterns=detected
        )

    def scan_document(self, chunks: List[TextChunk], filename: str) -> DocumentScanReport:
        """Scan all chunks of a document and tag quarantined chunks."""
        if not chunks:
            return DocumentScanReport(
                source_filename=filename,
                total_chunks=0,
                quarantined_chunks_count=0,
                clean_chunks_count=0,
                has_poisoned_content=False,
                verdicts=[]
            )

        verdicts: List[DocumentChunkVerdict] = []
        quarantined_count = 0

        for chunk in chunks:
            verdict = self.scan_chunk(chunk)
            verdicts.append(verdict)

            # Update chunk metadata directly with quarantine flag
            if verdict.is_poisoned:
                quarantined_count += 1
                chunk.metadata["is_quarantined"] = True
                chunk.metadata["quarantine_reason"] = verdict.quarantine_reason
            else:
                chunk.metadata.setdefault("is_quarantined", False)

        return DocumentScanReport(
            source_filename=filename,
            total_chunks=len(chunks),
            quarantined_chunks_count=quarantined_count,
            clean_chunks_count=len(chunks) - quarantined_count,
            has_poisoned_content=quarantined_count > 0,
            verdicts=verdicts
        )

