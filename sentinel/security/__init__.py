"""SENTINEL Security Engine Package.

Provides multi-barrier protection against prompt injection, document poisoning,
untrusted context manipulation, and secret egress leakage.
Owned by: Adhya (AI Security Engineer)
"""

from sentinel.security.normalizer import TextNormalizer, NormalizedResult
from sentinel.security.input_scanner import InputScanner, SecurityVerdict
from sentinel.security.document_scanner import DocumentScanner, DocumentScanReport, DocumentChunkVerdict
from sentinel.security.context_scanner import ContextScanner, ContextSecurityReport
from sentinel.security.egress_scanner import EgressScanner, EgressVerdict

__all__ = [
    "TextNormalizer",
    "NormalizedResult",
    "InputScanner",
    "SecurityVerdict",
    "DocumentScanner",
    "DocumentScanReport",
    "DocumentChunkVerdict",
    "ContextScanner",
    "ContextSecurityReport",
    "EgressScanner",
    "EgressVerdict",
]

