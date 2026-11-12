"""Input text normalization, canonicalization, and obfuscation decoding for SENTINEL.

Handles Unicode NFKD normalization, zero-width character stripping,
Base64 payload extraction & decoding, and Hex byte decoding.
Owned by: Adhya (AI Security Engineer)
"""

import base64
import binascii
import re
import unicodedata
from typing import List, Tuple
from pydantic import BaseModel, Field


class NormalizedResult(BaseModel):
    """Result of normalizing and de-obfuscating raw input text."""
    original_text: str = Field(..., description="Raw unmodified input text.")
    normalized_text: str = Field(..., description="Canonicalized and de-obfuscated text.")
    decoded_payloads: List[str] = Field(default_factory=list, description="Extracted obfuscated payloads.")
    has_obfuscation: bool = Field(default=False, description="Flag indicating if obfuscation was detected.")
    transformations_applied: List[str] = Field(default_factory=list, description="List of sanitizations applied.")


class TextNormalizer:
    """Canonicalizes input text and reveals obfuscated adversarial payloads."""

    # Zero-width and non-printing character regex
    ZERO_WIDTH_PATTERN = re.compile(
        r"[\u200B\u200C\u200D\u200E\u200F\uFEFF\u00AD\u2060\u2061\u2062\u2063\u2064]"
    )

    # Base64 pattern: minimum 16 valid characters with proper padding
    BASE64_PATTERN = re.compile(
        r"(?:[A-Za-z0-9+/]{4}){4,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"
    )

    # Hex sequence pattern: e.g. 69676e6f7265 (minimum 8 hex pairs) or \x69\x67...
    HEX_SLASH_PATTERN = re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}")
    HEX_RAW_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{2}){8,}\b")

    @classmethod
    def strip_zero_width_characters(cls, text: str) -> Tuple[str, bool]:
        """Strip invisible zero-width Unicode characters used for token splitting."""
        stripped = cls.ZERO_WIDTH_PATTERN.sub("", text)
        changed = len(stripped) != len(text)
        return stripped, changed

    @classmethod
    def canonicalize_unicode(cls, text: str) -> Tuple[str, bool]:
        """Apply Unicode NFKD normalization to map confusable homoglyphs to ASCII.
        
        For example: Cyrillic 'а' (\u0430) -> Latin 'a' (\u0061),
        Full-width characters -> Half-width equivalents.
        """
        # NFKD decomposes characters into compatibility components
        nfkd_form = unicodedata.normalize("NFKD", text)
        # Encode to ASCII bytes with ignore, then decode back to normalize homoglyphs where possible
        ascii_text = "".join(
            c for c in nfkd_form if not unicodedata.combining(c)
        )
        changed = ascii_text != text
        return ascii_text, changed

    @classmethod
    def extract_and_decode_base64(cls, text: str) -> List[str]:
        """Find and decode valid Base64 encoded strings."""
        decoded_payloads: List[str] = []
        matches = cls.BASE64_PATTERN.findall(text)
        for match in matches:
            if len(match) < 16:
                continue
            try:
                raw_bytes = base64.b64decode(match, validate=True)
                # Attempt decoding to readable UTF-8
                decoded_str = raw_bytes.decode("utf-8").strip()
                # Check if decoded string looks like readable text (at least 70% printable)
                if len(decoded_str) >= 4 and sum(c.isprintable() for c in decoded_str) / len(decoded_str) > 0.7:
                    decoded_payloads.append(decoded_str)
            except (binascii.Error, UnicodeDecodeError):
                continue
        return decoded_payloads

    @classmethod
    def extract_and_decode_hex(cls, text: str) -> List[str]:
        """Find and decode hexadecimal strings."""
        decoded_payloads: List[str] = []

        # 1. Escaped hex sequences: \x69\x67\x6e...
        slash_matches = cls.HEX_SLASH_PATTERN.findall(text)
        for match in slash_matches:
            clean_hex = match.replace("\\x", "")
            try:
                decoded = bytes.fromhex(clean_hex).decode("utf-8", errors="ignore").strip()
                if len(decoded) >= 4 and sum(c.isprintable() for c in decoded) / len(decoded) > 0.7:
                    decoded_payloads.append(decoded)
            except (ValueError, UnicodeDecodeError):
                continue

        # 2. Raw hex blocks: 69676e6f7265...
        raw_matches = cls.HEX_RAW_PATTERN.findall(text)
        for match in raw_matches:
            try:
                decoded = bytes.fromhex(match).decode("utf-8", errors="ignore").strip()
                if len(decoded) >= 4 and sum(c.isprintable() for c in decoded) / len(decoded) > 0.7:
                    decoded_payloads.append(decoded)
            except (ValueError, UnicodeDecodeError):
                continue

        return decoded_payloads

    @classmethod
    def normalize(cls, text: str) -> NormalizedResult:
        """Run complete multi-stage canonicalization and de-obfuscation pipeline."""
        if not text:
            return NormalizedResult(
                original_text="",
                normalized_text="",
                decoded_payloads=[],
                has_obfuscation=False,
                transformations_applied=[]
            )

        transformations = []
        current_text = text

        # 1. Zero-width character stripping
        current_text, changed_zw = cls.strip_zero_width_characters(current_text)
        if changed_zw:
            transformations.append("zero_width_stripped")

        # 2. Unicode NFKD Canonicalization
        current_text, changed_nfkd = cls.canonicalize_unicode(current_text)
        if changed_nfkd:
            transformations.append("unicode_nfkd_normalized")

        # 3. Base64 de-obfuscation
        b64_payloads = cls.extract_and_decode_base64(text)
        if b64_payloads:
            transformations.append(f"base64_decoded_{len(b64_payloads)}_payloads")

        # 4. Hex de-obfuscation
        hex_payloads = cls.extract_and_decode_hex(text)
        if hex_payloads:
            transformations.append(f"hex_decoded_{len(hex_payloads)}_payloads")

        all_decoded = b64_payloads + hex_payloads
        has_obfuscation = bool(transformations)

        # Append decoded payloads to normalized text for downstream heuristic scanning
        if all_decoded:
            current_text = f"{current_text}\n[DECODED_OBSCURATION]: " + " | ".join(all_decoded)

        return NormalizedResult(
            original_text=text,
            normalized_text=current_text,
            decoded_payloads=all_decoded,
            has_obfuscation=has_obfuscation,
            transformations_applied=transformations
        )

