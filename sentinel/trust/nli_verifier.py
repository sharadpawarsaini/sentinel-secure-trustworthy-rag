"""Natural Language Inference (NLI) Claim Verifier for SENTINEL.

Evaluates claim-level entailment, neutral grounding, and contradiction against
retrieved evidence context using local Cross-Encoder models.
Owned by: Anwesha (Trust, Hallucination and NLI Engineer)
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.rag.vector_store import RetrievedChunk


class ClaimNLIResult(BaseModel):
    """NLI verification result for an individual atomic claim."""
    claim: str = Field(..., description="The atomic claim evaluated.")
    verdict: str = Field(..., description="ENTAILED, CONTRADICTED, or NEUTRAL.")
    entailment_prob: float = Field(..., description="Probability of entailment in [0.0, 1.0].")
    neutral_prob: float = Field(..., description="Probability of neutral/unmentioned in [0.0, 1.0].")
    contradiction_prob: float = Field(..., description="Probability of direct contradiction in [0.0, 1.0].")
    best_supporting_chunk_id: Optional[str] = Field(None, description="Chunk providing highest entailment.")
    best_supporting_source: Optional[str] = Field(None, description="Filename of supporting evidence.")


class NLIReport(BaseModel):
    """Aggregate NLI report for all claims extracted from an answer."""
    claims_count: int
    entailed_claims_count: int
    contradicted_claims_count: int
    neutral_claims_count: int
    overall_faithfulness_ratio: float = Field(..., description="Ratio of entailed claims to total claims.")
    has_critical_contradiction: bool = Field(default=False, description="True if any claim is directly contradicted.")
    claim_results: List[ClaimNLIResult] = Field(default_factory=list)


class NLIVerifier:
    """NLI cross-encoder verifier evaluating claim entailment against evidence."""

    DEFAULT_MODEL = "cross-encoder/nli-deberta-v3-small"

    def __init__(
        self,
        model_name: Optional[str] = None,
        contra_threshold: float = 0.55,
        entail_threshold: float = 0.50,
        use_mock: Optional[bool] = None
    ):
        """Initialize NLI verifier.

        Args:
            model_name: Hugging Face cross-encoder model name.
            contra_threshold: Threshold above which a claim is deemed CONTRADICTED.
            entail_threshold: Threshold above which a claim is deemed ENTAILED.
            use_mock: If True, uses deterministic lexical inference for instant testing.
                Defaults to settings.low_memory_mode when None.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.contra_threshold = contra_threshold
        self.entail_threshold = entail_threshold
        self.use_mock = settings.low_memory_mode if use_mock is None else use_mock
        self._model = None
        self._tokenizer = None

    def _lazy_load_model(self):
        """Lazy load HuggingFace CrossEncoder on demand."""
        if self._model is None and not self.use_mock:
            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(device)
                self._model.eval()
            except Exception as e:
                # If network fails or model is not cached, gracefully switch to deterministic heuristic fallback
                self.use_mock = True

    def _heuristic_nli(self, premise: str, hypothesis: str) -> Tuple[float, float, float]:
        """Deterministic lexical overlap & negation heuristic for fast testing."""
        hyp_words = set(hypothesis.lower().split())
        prem_words = set(premise.lower().split())

        # Contradiction indicators: presence of antonyms or negations
        negations = {"not", "never", "no", "cannot", "refuse", "disagree", "unauthorized"}
        hyp_has_neg = bool(hyp_words.intersection(negations))
        prem_has_neg = bool(prem_words.intersection(negations))

        # Check word overlap
        overlap = len(hyp_words.intersection(prem_words)) / max(1, len(hyp_words))

        if hyp_has_neg != prem_has_neg and overlap > 0.40:
            # High overlap but polarity mismatch indicates contradiction
            return (0.10, 0.20, 0.70)
        elif overlap >= 0.50:
            # Significant factual overlap indicates entailment
            return (round(min(0.95, overlap * 1.1), 3), 0.15, 0.05)
        elif overlap >= 0.25:
            # Partial overlap is neutral / partially supported
            return (0.35, 0.55, 0.10)
        else:
            # Very low overlap is unmentioned / neutral
            return (0.10, 0.85, 0.05)

    def verify_claim(
        self,
        claim: str,
        context_chunks: List[RetrievedChunk]
    ) -> ClaimNLIResult:
        """Verify an atomic claim against all retrieved context chunks."""
        # Handle abstention string directly
        if "i do not have sufficient information" in claim.lower():
            return ClaimNLIResult(
                claim=claim,
                verdict="ENTAILED",
                entailment_prob=1.0,
                neutral_prob=0.0,
                contradiction_prob=0.0,
                best_supporting_chunk_id=None,
                best_supporting_source="abstention_protocol"
            )

        if not context_chunks:
            return ClaimNLIResult(
                claim=claim,
                verdict="NEUTRAL",
                entailment_prob=0.0,
                neutral_prob=1.0,
                contradiction_prob=0.0,
                best_supporting_chunk_id=None,
                best_supporting_source=None
            )

        self._lazy_load_model()

        best_entailment = 0.0
        worst_contradiction = 0.0
        best_chunk_id = None
        best_source = None

        for chunk in context_chunks:
            premise = chunk.text
            hypothesis = claim

            if self.use_mock or self._model is None:
                p_entail, p_neutral, p_contra = self._heuristic_nli(premise, hypothesis)
            else:
                import torch
                # Run neural CrossEncoder forward pass
                inputs = self._tokenizer(
                    premise,
                    hypothesis,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self._model.device)

                with torch.no_grad():
                    logits = self._model(**inputs).logits
                    probs = torch.softmax(logits, dim=-1)[0].tolist()

                # Model label mapping for DeBERTa: 0: contradiction, 1: entailment, 2: neutral
                p_contra = probs[0]
                p_entail = probs[1]
                p_neutral = probs[2]

            if p_contra > worst_contradiction:
                worst_contradiction = p_contra

            if p_entail > best_entailment:
                best_entailment = p_entail
                best_chunk_id = chunk.chunk_id
                best_source = chunk.source_filename

        # Classify verdict
        if worst_contradiction >= self.contra_threshold:
            verdict = "CONTRADICTED"
        elif best_entailment >= self.entail_threshold:
            verdict = "ENTAILED"
        else:
            verdict = "NEUTRAL"

        neutral_p = round(max(0.0, 1.0 - best_entailment - worst_contradiction), 4)

        return ClaimNLIResult(
            claim=claim,
            verdict=verdict,
            entailment_prob=round(best_entailment, 4),
            neutral_prob=neutral_p,
            contradiction_prob=round(worst_contradiction, 4),
            best_supporting_chunk_id=best_chunk_id,
            best_supporting_source=best_source
        )

    def verify_answer(
        self,
        claims: List[str],
        context_chunks: List[RetrievedChunk]
    ) -> NLIReport:
        """Verify all atomic claims extracted from an answer."""
        if not claims:
            return NLIReport(
                claims_count=0,
                entailed_claims_count=0,
                contradicted_claims_count=0,
                neutral_claims_count=0,
                overall_faithfulness_ratio=0.0,
                has_critical_contradiction=False,
                claim_results=[]
            )

        results = [self.verify_claim(c, context_chunks) for c in claims]

        entailed = sum(1 for r in results if r.verdict == "ENTAILED")
        contradicted = sum(1 for r in results if r.verdict == "CONTRADICTED")
        neutral = sum(1 for r in results if r.verdict == "NEUTRAL")

        # Faithfulness ratio
        faithfulness = round(entailed / len(claims), 4) if claims else 0.0
        has_contra = contradicted > 0

        return NLIReport(
            claims_count=len(claims),
            entailed_claims_count=entailed,
            contradicted_claims_count=contradicted,
            neutral_claims_count=neutral,
            overall_faithfulness_ratio=faithfulness,
            has_critical_contradiction=has_contra,
            claim_results=results
        )

