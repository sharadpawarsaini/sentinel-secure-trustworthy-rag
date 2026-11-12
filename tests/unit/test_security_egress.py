"""Unit tests for Output and Egress Security Scanner (Component 3.5).

Owned by: Adhya (AI Security Engineer)
"""

import pytest
from sentinel.security.egress_scanner import EgressScanner


def test_egress_scanner_clean_output():
    scanner = EgressScanner()
    clean_output = "Employees are entitled to 25 days of annual vacation leave."
    verdict = scanner.scan(clean_output)
    assert verdict.is_safe is True
    assert verdict.has_leakage is False
    assert verdict.sanitized_text == clean_output


def test_egress_scanner_redacts_api_keys():
    scanner = EgressScanner()
    leaky_output = "Here is your key: sk-abcdef1234567890abcdef1234567890abcdef please keep it safe."
    verdict = scanner.scan(leaky_output)
    assert verdict.is_safe is False
    assert verdict.has_leakage is True
    assert "sk-" not in verdict.sanitized_text
    assert "[REDACTED_OPENAI_API_KEY]" in verdict.sanitized_text


def test_egress_scanner_blocks_system_prompt_regurgitation():
    scanner = EgressScanner(system_prompt_leak_threshold=0.60)
    system_prompt = (
        "You are a helpful and strictly factual AI assistant for the SENTINEL system. "
        "Answer the user's question based strictly on the retrieved context provided below. "
        "Do not speculate, assume, or extrapolate beyond the facts directly provided."
    )
    regurgitated_output = (
        "My instructions are: You are a helpful and strictly factual AI assistant for the SENTINEL system. "
        "Answer the user's question based strictly on the retrieved context provided below."
    )
    verdict = scanner.scan(regurgitated_output, system_prompt=system_prompt)
    assert verdict.is_safe is False
    assert "system_prompt_leakage" in "; ".join(verdict.violations)
    assert "confidential system instructions" in verdict.sanitized_text

