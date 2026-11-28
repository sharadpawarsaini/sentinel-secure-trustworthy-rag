"""Dense embedding model wrapper for SENTINEL.

Integrates Hugging Face SentenceTransformers for local, deterministic vector embeddings,
with a lazy-loading architecture and a zero-PyTorch low-memory mode for constrained
cloud environments (e.g., Render 512 MiB Free Tier).
Owned by: Bhumika (RAG Foundation)
"""

import hashlib
import re
from typing import List, Optional, Any
import numpy as np
from sentinel.config import settings


class EmbeddingEngine:
    """Singleton wrapper for local dense sentence embeddings."""

    _instance: Optional["EmbeddingEngine"] = None
    _model: Optional[Any] = None
    LIGHTWEIGHT_DIM = 384

    def __init__(self, model_name: Optional[str] = None, low_memory: Optional[bool] = None):
        """Initialize the embedding engine.

        Args:
            model_name: Name or path of the SentenceTransformer model.
            low_memory: If True, uses a lightweight 384-d NumPy n-gram hashing embedder
                without importing PyTorch or SentenceTransformers.
        """
        self.model_name = model_name or settings.embedding_model_name
        self.low_memory = settings.low_memory_mode if low_memory is None else low_memory
        self._device: Optional[str] = None

    @property
    def model(self) -> Any:
        """Lazy-loaded SentenceTransformer model."""
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = SentenceTransformer(self.model_name, device=self._device)
        return self._model

    @property
    def dimension(self) -> int:
        """Return the vector dimensionality of the embedding model."""
        if self.low_memory:
            return self.LIGHTWEIGHT_DIM
        if hasattr(self.model, "get_embedding_dimension"):
            dim = self.model.get_embedding_dimension()
        else:
            dim = self.model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else self.LIGHTWEIGHT_DIM

    def _lightweight_embed(self, text: str) -> List[float]:
        """Zero-PyTorch 384-d signed feature-hashing embedder over words and char trigrams."""
        vec = np.zeros(self.LIGHTWEIGHT_DIM, dtype=np.float32)
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            vec[0] = 1.0
            return vec.tolist()

        features: List[tuple[str, float]] = []
        for tok in tokens:
            features.append((f"w:{tok}", 1.5))
            if len(tok) >= 3:
                for i in range(len(tok) - 2):
                    features.append((f"c:{tok[i:i+3]}", 0.5))

        for feat, weight in features:
            digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(digest[:4], "little") % self.LIGHTWEIGHT_DIM
            sign = 1.0 if (digest[4] & 1) == 0 else -1.0
            vec[idx] += sign * weight

        norm = float(np.linalg.norm(vec))
        if norm > 0.0:
            vec /= norm
        else:
            vec[0] = 1.0
        return vec.tolist()

    def embed_text(self, text: str) -> List[float]:
        """Generate a dense embedding vector for a single string.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the dense vector.
        """
        clean_text = text.strip() or " "
        if self.low_memory:
            return self._lightweight_embed(clean_text)

        vector = self.model.encode(
            clean_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return vector.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate dense embeddings for a batch of strings.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of items per batch.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        clean_texts = [t.strip() or " " for t in texts]
        if self.low_memory:
            return [self._lightweight_embed(t) for t in clean_texts]

        vectors = self.model.encode(
            clean_texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return vectors.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two normalized vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


def get_embedding_engine(model_name: Optional[str] = None) -> EmbeddingEngine:
    """Return the global EmbeddingEngine singleton."""
    if EmbeddingEngine._instance is None:
        EmbeddingEngine._instance = EmbeddingEngine(model_name=model_name)
    return EmbeddingEngine._instance
