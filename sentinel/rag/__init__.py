"""SENTINEL RAG foundation module (Bhumika's component)."""

from sentinel.rag.document_loader import DocumentLoader, LoadedDocument
from sentinel.rag.chunker import TextChunker, TextChunk
from sentinel.rag.embedder import EmbeddingEngine, get_embedding_engine
from sentinel.rag.vector_store import VectorStoreManager, RetrievedChunk
from sentinel.rag.generator import (
    BaselineGenerator,
    GenerationResult,
    BaseLLMClient,
    MockLLMClient,
    OllamaClient,
    get_llm_client
)

__all__ = [
    "DocumentLoader",
    "LoadedDocument",
    "TextChunker",
    "TextChunk",
    "EmbeddingEngine",
    "get_embedding_engine",
    "VectorStoreManager",
    "RetrievedChunk",
    "BaselineGenerator",
    "GenerationResult",
    "BaseLLMClient",
    "MockLLMClient",
    "OllamaClient",
    "get_llm_client"
]
