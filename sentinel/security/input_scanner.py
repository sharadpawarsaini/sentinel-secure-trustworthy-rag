"""Input Prompt Injection and Jailbreak Heuristic Scanner for SENTINEL.

Detects direct prompt injections, instruction overrides, delimiter escapes,
system prompt probing, and adversarial roleplay jailbreaks.
Owned by: Adhya (AI Security Engineer)
"""

import re
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.security.normalizer import TextNormalizer, NormalizedResult


class SecurityVerdict(BaseModel):
    """Structured security evaluation returned for an input text."""
    is_malicious: bool = Field(..., description="True if risk exceeds block threshold.")
    risk_score: float = Field(..., description="Calibrated risk score in [0.0, 1.0].")
    action: Literal["PASS", "FLAG", "BLOCK"] = Field(..., description="Security barrier action.")
    attack_category: Optional[str] = Field(None, description="Classified attack category if flagged.")
    matched_patterns: List[str] = Field(default_factory=list, description="Specific attack signatures triggered.")
    details: Dict[str, str] = Field(default_factory=dict, description="Diagnostic audit details.")


class InputScanner:
    """Multi-pattern signature and heuristic scanner for user inputs."""

    # Threat Signatures with calibrated risk weights
    # Category 1: Direct Instruction Overrides (High severity: 0.85)
    INSTRUCTION_OVERRIDE_RULES = [
        (re.compile(r"\b(?:ignore|disregard|forget|bypass)\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules|constraints|context)\b", re.I), "instruction_override", 0.90),
        (re.compile(r"\b(?:override|reset|clear)\s+(?:system\s+)?(?:instructions|prompt|rules)\b", re.I), "system_instruction_override", 0.85),
        (re.compile(r"\bfrom\s+now\s+on(?:,|:)?\s+(?:you\s+must|you\s+will|act\s+as|only\s+answer)\b", re.I), "behavioral_hijack", 0.75),
        (re.compile(r"\b(?:new|updated)\s+(?:system\s+)?instructions\s*:", re.I), "injected_instruction_header", 0.80),
        (re.compile(r"\bdo\s+not\s+follow\s+(?:the\s+)?(?:system|developer|safety)\s+(?:guidelines|rules|instructions)\b", re.I), "safety_rule_bypass", 0.85),
    ]

    # Category 2: Delimiter Hijacking & Format Smuggling (High severity: 0.80)
    DELIMITER_HIJACK_RULES = [
        (re.compile(r"</(?:system|user_input|context|instruction|context_document|context_chunk)>", re.I), "closing_tag_injection", 0.85),
        (re.compile(r"<(?:system|admin|override|sentinel_command)>", re.I), "privileged_tag_injection", 0.85),
        (re.compile(r"(?:\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>)", re.I), "llama_special_token_injection", 0.90),
        (re.compile(r"(?:<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>)", re.I), "chatml_token_injection", 0.95),
        (re.compile(r"---END\s+OF\s+(?:SYSTEM\s+PROMPT|CONTEXT|INSTRUCTIONS)---", re.I), "delimiter_spoofing", 0.80),
    ]

    # Category 3: System Prompt Extraction & Secret Probing (Medium-High severity: 0.75)
    EXTRACTION_PROBE_RULES = [
        (re.compile(r"\b(?:repeat|print|reveal|output|display|show|leak)\s+(?:the\s+)?(?:system\s+prompt|initial\s+instructions|system\s+instructions|developer\s+prompt)\b", re.I), "system_prompt_probing", 0.80),
        (re.compile(r"\bwhat\s+(?:are|were)\s+your\s+(?:initial|original|system)\s+instructions\b", re.I), "prompt_leak_query", 0.70),
        (re.compile(r"\boutput\s+everything\s+above\s+(?:verbatim|starting\s+with)\b", re.I), "verbatim_prefix_probe", 0.85),
        (re.compile(r"\bshow\s+(?:me\s+)?(?:your\s+)?(?:api\s*keys?|secret\s*tokens?|credentials)\b", re.I), "credential_harvesting_probe", 0.85),
    ]

    # Category 4: Adversarial Roleplay & Jailbreaks (Medium-High severity: 0.75)
    JAILBREAK_RULES = [
        (re.compile(r"\b(?:DAN\s+mode|Do\s+Anything\s+Now|unrestricted\s+AI|jailbroken)\b", re.I), "dan_jailbreak_heuristic", 0.90),
        (re.compile(r"\bdeveloper\s+debug\s+mode\s+(?:is\s+)?enabled\b", re.I), "developer_mode_simulation", 0.85),
        (re.compile(r"\bhypothetical\s+fictional\s+scenario\s+where\s+(?:all\s+)?(?:rules|morals|ethics)\s+are\s+suspended\b", re.I), "fictional_unrestricted_scenario", 0.80),
        (re.compile(r"\byou\s+are\s+now\s+in\s+god\s+mode\b", re.I), "godmode_jailbreak", 0.85),
    ]

    def __init__(
        self,
        block_threshold: Optional[float] = None,
        flag_threshold: float = 0.40
    ):
        """Initialize the input security scanner.

        Args:
            block_threshold: Risk score above which input is blocked (default: settings.security_risk_threshold).
            flag_threshold: Risk score above which input is flagged for auditing.
        """
        self.block_threshold = block_threshold or settings.security_risk_threshold
        self.flag_threshold = flag_threshold

        # Assemble unified rule bank
        self.all_rules = (
            self.INSTRUCTION_OVERRIDE_RULES +
            self.DELIMITER_HIJACK_RULES +
            self.EXTRACTION_PROBE_RULES +
            self.JAILBREAK_RULES
        )

    def scan(self, text: str) -> SecurityVerdict:
        """Scan input query through normalization and multi-category heuristic analysis."""
        if not text or not text.strip():
            return SecurityVerdict(
                is_malicious=False,
                risk_score=0.0,
                action="PASS",
                attack_category=None,
                matched_patterns=[],
                details={"reason": "Empty input"}
            )

        # 1. Normalize input to eliminate obfuscations
        normalized_res: NormalizedResult = TextNormalizer.normalize(text)
        scan_target = normalized_res.normalized_text

        matched_signatures: List[str] = []
        accumulated_risk = 0.0
        primary_category: Optional[str] = None
        category_counts: Dict[str, int] = {}

        # 2. Add penalty if obfuscation was detected
        if normalized_res.has_obfuscation:
            matched_signatures.append(f"obfuscation_detected({','.join(normalized_res.transformations_applied)})")
            accumulated_risk += 0.35
            category_counts["obfuscation"] = 1

        # 3. Evaluate regex patterns against normalized text
        for pattern, category, weight in self.all_rules:
            match = pattern.search(scan_target)
            if match:
                matched_signatures.append(f"{category}:{match.group(0)}")
                accumulated_risk += weight
                category_counts[category] = category_counts.get(category, 0) + 1
                if primary_category is None:
                    primary_category = category

        # Calibrate risk score to [0.0, 1.0] using diminishing returns for multiple matches
        # Formula: calibrated_risk = 1.0 - (1.0 - min(accumulated_risk, 0.99))^1.2
        calibrated_risk = min(1.0, round(accumulated_risk, 4))

        # Determine action
        if calibrated_risk >= self.block_threshold:
            action = "BLOCK"
            is_malicious = True
        elif calibrated_risk >= self.flag_threshold:
            action = "FLAG"
            is_malicious = False
        else:
            action = "PASS"
            is_malicious = False

        return SecurityVerdict(
            is_malicious=is_malicious,
            risk_score=calibrated_risk,
            action=action,
            attack_category=primary_category,
            matched_patterns=matched_signatures,
            details={
                "has_obfuscation": str(normalized_res.has_obfuscation),
                "transformations": str(normalized_res.transformations_applied),
                "block_threshold": str(self.block_threshold)
            }
        )

