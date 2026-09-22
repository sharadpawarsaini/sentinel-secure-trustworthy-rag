"""Persistent ChromaDB vector store manager for SENTINEL.

Handles chunk indexing, embedding persistence, and cosine similarity top-K retrieval.
Owned by: Bhumika (RAG Foundation)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.rag.chunker import TextChunk
from sentinel.rag.embedder import get_embedding_engine, EmbeddingEngine


class RetrievedChunk(BaseModel):
    """Structured representation of a retrieved evidence chunk."""
    chunk_id: str = Field(..., description="Unique chunk identifier.")
    text: str = Field(..., description="Text content of the retrieved chunk.")
    source_filename: str = Field(..., description="Originating document filename.")
    chunk_index: int = Field(..., description="Index position in parent document.")
    similarity_score: float = Field(..., description="Cosine similarity score in [0.0, 1.0].")
    distance: float = Field(..., description="Raw vector distance from ChromaDB.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary.")


class VectorStoreManager:
    """Manages persistent ChromaDB vector storage and semantic search."""

    DEFAULT_COLLECTION = "sentinel_knowledge_base"

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedder: Optional[EmbeddingEngine] = None
    ):
        """Initialize ChromaDB client and collection.

        Args:
            persist_dir: Directory path for persistent database storage.
            collection_name: Name of the vector collection.
            embedder: EmbeddingEngine instance for generating vectors.
        """
        self.persist_dir = Path(persist_dir or settings.vector_store_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or self.DEFAULT_COLLECTION
        self.embedder = embedder or get_embedding_engine()

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get or create collection with cosine similarity metric
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        chunks: List[TextChunk],
        embeddings: Optional[List[List[float]]] = None
    ) -> int:
        """Upsert text chunks and their embeddings into ChromaDB.

        Args:
            chunks: List of TextChunk objects to store.
            embeddings: Optional pre-computed embeddings. Computed if None.

        Returns:
            Count of chunks successfully added/updated.
        """
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]

        # Sanitize metadata for ChromaDB (only allows primitive str, int, float, bool)
        metadatas: List[Dict[str, Any]] = []
        for chunk in chunks:
            meta: Dict[str, Any] = {
                "source_filename": str(chunk.source_filename),
                "chunk_index": int(chunk.chunk_index),
                "start_char": int(chunk.start_char),
                "end_char": int(chunk.end_char),
                "character_count": int(chunk.character_count)
            }
            # Flatten additional metadata keys safely
            for k, v in chunk.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            metadatas.append(meta)

        # Compute embeddings if not provided
        if embeddings is None:
            embeddings = self.embedder.embed_batch(documents)

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return len(chunks)

    def query_similar(
        self,
        query_text: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """Perform semantic similarity search over stored chunks.

        Args:
            query_text: Natural language user query.
            top_k: Number of nearest neighbors to retrieve.
            score_threshold: Minimum similarity threshold in [0.0, 1.0].

        Returns:
            List of RetrievedChunk objects ordered by descending similarity.
        """
        clean_query = query_text.strip()
        if not clean_query or self.collection.count() == 0:
            return []

        # Generate query vector
        query_vector = self.embedder.embed_text(clean_query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        retrieved: List[RetrievedChunk] = []

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
            # ChromaDB cosine distance d in [0, 2]; similarity = 1.0 - d
            distance_val = float(dist) if dist is not None else 1.0
            similarity_val = max(0.0, min(1.0, 1.0 - distance_val))

            if score_threshold is not None and similarity_val < score_threshold:
                continue

            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=doc_text,
                    source_filename=str(meta.get("source_filename", "unknown")),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    similarity_score=round(similarity_val, 4),
                    distance=round(distance_val, 4),
                    metadata=meta
                )
            )

        # Sort by similarity score descending
        retrieved.sort(key=lambda x: x.similarity_score, reverse=True)
        return retrieved

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return operational statistics for the vector store."""
        total_chunks = self.collection.count()
        unique_docs = set()

        if total_chunks > 0:
            # Peek to inspect document metadata
            peek_data = self.collection.get(include=["metadatas"])
            for meta in peek_data.get("metadatas", []):
                if meta and "source_filename" in meta:
                    unique_docs.add(meta["source_filename"])

        return {
            "collection_name": self.collection_name,
            "storage_path": str(self.persist_dir),
            "total_chunks": total_chunks,
            "unique_documents_count": len(unique_docs),
            "unique_documents": sorted(list(unique_docs))
        }

    def delete_document(self, source_filename: str) -> int:
        """Delete all chunks belonging to a specific document.

        Args:
            source_filename: Filename of the document to purge.

        Returns:
            Number of chunks removed.
        """
        matching = self.collection.get(
            where={"source_filename": source_filename},
            include=["metadatas"]
        )
        matching_ids = matching.get("ids", [])
        if matching_ids:
            self.collection.delete(ids=matching_ids)
        return len(matching_ids)

    def clear_collection(self) -> None:
        """Clear all stored vectors from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
