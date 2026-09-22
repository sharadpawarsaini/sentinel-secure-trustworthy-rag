"""Dense embedding model wrapper for SENTINEL.

Integrates Hugging Face SentenceTransformers for local, deterministic vector embeddings.
Owned by: Bhumika (RAG Foundation)
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from sentinel.config import settings


class EmbeddingEngine:
    """Singleton wrapper for local dense sentence embeddings."""

    _instance: Optional["EmbeddingEngine"] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding engine.

        Args:
            model_name: Name or path of the SentenceTransformer model.
        """
        self.model_name = model_name or settings.embedding_model_name
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-loaded SentenceTransformer model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self._device)
        return self._model

    @property
    def dimension(self) -> int:
        """Return the vector dimensionality of the embedding model."""
        if hasattr(self.model, "get_embedding_dimension"):
            dim = self.model.get_embedding_dimension()
        else:
            dim = self.model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384

    def embed_text(self, text: str) -> List[float]:
        """Generate a dense embedding vector for a single string.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the dense vector.
        """
        clean_text = text.strip() or " "
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
