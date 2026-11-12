"""Query Reformulation and Re-Retrieval Engine for SENTINEL.

Rewrites low-confidence or ambiguous queries to improve dense retrieval precision.
Owned by: Sharad (System Architect & Integration Engineer)
"""

import re
from typing import List


class QueryReformulator:
    """Reformulates queries to maximize retrieval recall and precision."""

    # Words to strip when optimizing semantic queries
    STOP_PHRASES = [
        re.compile(r"^(?:can you\s+|could you\s+|please\s+|tell me\s+|i want to know\s+|what is\s+|what are\s+)", re.I),
        re.compile(r"\b(?:in detail|accurately|briefly|as per the document)\b", re.I),
    ]

    @classmethod
    def reformulate(cls, original_query: str) -> str:
        """Reformulate query by removing conversational noise and emphasizing key entities."""
        cleaned = original_query.strip()
        for phrase in cls.STOP_PHRASES:
            cleaned = phrase.sub("", cleaned).strip()

        # If stripping made it too short, retain original
        if len(cleaned) < 5:
            return original_query.strip()

        # Return standardized query
        return cleaned

