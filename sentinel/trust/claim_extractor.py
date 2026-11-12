"""Atomic claim and proposition extractor for SENTINEL Trust Engine.

Decomposes generated LLM answers into verifiable atomic claims for NLI verification.
Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

import re
from typing import List


class ClaimExtractor:
    """Decomposes multi-sentence answers into atomic factual claims."""

    # Sentence boundary regex (handles punctuation followed by whitespace and capital letter)
    SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])")

    # Conversational filler and non-factual introductory phrases
    FILLER_PREFIXES = [
        re.compile(r"^(?:sure|certainly|of course|based on the (?:provided )?context|according to the text|as mentioned in the text|in summary|to answer your question)[,:]?\s*", re.I),
        re.compile(r"^(?:here is the answer|the answer is|here is|the following is|in conclusion)[,:]?\s*", re.I),
        re.compile(r"^(?:the answer:)\s*", re.I),
    ]

    # Markdown bullet / numbered list prefixes
    LIST_PREFIX = re.compile(r"^(?:[\*\-\+]|\d+[\.\)])\s+")

    @classmethod
    def clean_claim(cls, sentence: str) -> str:
        """Strip conversational fluff and markdown list tokens."""
        text = sentence.strip()
        # Remove list markers like "1. " or "- "
        text = cls.LIST_PREFIX.sub("", text).strip()
        # Repeatedly remove conversational filler prefixes
        changed = True
        while changed:
            original = text
            for filler_re in cls.FILLER_PREFIXES:
                text = filler_re.sub("", text).strip()
            changed = (text != original)
        return text

    @classmethod
    def is_header_or_fluff(cls, text: str) -> bool:
        """Check if string is just a header or fluff without factual assertions."""
        stripped = text.strip()
        if not stripped:
            return True
        # Lines ending with a colon with no complete clause (e.g. "Here is the answer:")
        if stripped.endswith(":") and len(stripped.split()) <= 6:
            return True
        # Pure introductory markers
        if re.match(r"^(?:the answer|answers?|summary|key points?)[:.]?$", stripped, re.I):
            return True
        return False

    @classmethod
    def extract_claims(cls, answer_text: str) -> List[str]:
        """Extract a list of atomic factual statements from an answer.
        
        Args:
            answer_text: Full generated answer text from LLM.

        Returns:
            List of non-empty factual claim strings.
        """
        if not answer_text or not answer_text.strip():
            return []

        # Check for abstention sentences
        lower_ans = answer_text.lower().strip()
        if "i do not have sufficient information" in lower_ans or "not enough information" in lower_ans:
            return ["I do not have sufficient information in the provided context to answer this question."]

        # Split across newlines and punctuation
        raw_lines = answer_text.strip().split("\n")
        candidate_sentences: List[str] = []

        for line in raw_lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if entire line is just a conversational header
            cleaned_line = cls.clean_claim(line_clean)
            if cls.is_header_or_fluff(cleaned_line):
                continue

            # Split line into sentences
            splits = cls.SENTENCE_SPLIT_REGEX.split(line_clean)
            for s in splits:
                cleaned = cls.clean_claim(s)
                if cls.is_header_or_fluff(cleaned):
                    continue
                # Filter out very short fragments (< 10 chars)
                if len(cleaned) >= 10:
                    candidate_sentences.append(cleaned)

        # Fallback: if no sentences qualified, return whole stripped answer
        if not candidate_sentences and len(answer_text.strip()) > 0:
            candidate_sentences.append(answer_text.strip())

        return candidate_sentences
