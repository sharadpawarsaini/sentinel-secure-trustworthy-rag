"""Pydantic API request and response schemas for SENTINEL."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response returned after successful document ingestion."""
    filename: str = Field(..., description="Uploaded document filename.")
    file_type: str = Field(..., description="File format extension (.pdf, .docx, .txt).")
    character_count: int = Field(..., description="Extracted plain text character count.")
    chunks_created: int = Field(..., description="Number of chunks generated and indexed.")
    status: str = Field(default="indexed", description="Ingestion status.")


class QueryRequest(BaseModel):
    """Payload submitted when asking a question."""
    query: str = Field(..., min_length=1, description="Natural language question to ask.")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of evidence chunks to retrieve.")
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum cosine similarity cutoff.")
    provider: Optional[str] = Field(default=None, description="Optional LLM backend override ('ollama', 'mock').")


class ChunkEvidence(BaseModel):
    """Retrieved evidence chunk schema for API response."""
    chunk_id: str = Field(..., description="Deterministic SHA-256 chunk identifier.")
    source_filename: str = Field(..., description="Originating document filename.")
    chunk_index: int = Field(..., description="Chunk index in original document.")
    similarity_score: float = Field(..., description="Cosine similarity score in [0.0, 1.0].")
    text: str = Field(..., description="Text content of this chunk.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata.")


class QueryResponse(BaseModel):
    """Response returned after RAG retrieval and generation."""
    query: str = Field(..., description="Original question submitted.")
    answer: str = Field(..., description="Generated answer text.")
    retrieved_chunks: List[ChunkEvidence] = Field(default_factory=list, description="Evidence chunks used.")
    model: str = Field(..., description="Model identifier used for generation.")
    provider: str = Field(..., description="LLM provider name.")
    latency_ms: float = Field(..., description="Total roundtrip pipeline latency in milliseconds.")
    pipeline_mode: str = Field(default="BASELINE_RAG", description="Active pipeline operational mode.")


class DocumentListResponse(BaseModel):
    """Collection overview and statistics."""
    total_chunks: int = Field(..., description="Total chunks in persistent vector index.")
    unique_documents_count: int = Field(..., description="Total unique documents indexed.")
    unique_documents: List[str] = Field(default_factory=list, description="List of indexed document filenames.")
    collection_name: str = Field(..., description="Vector store collection name.")


class HealthResponse(BaseModel):
    """System health status."""
    status: str = Field(default="healthy")
    version: str = Field(default="0.1.0")
    llm_provider: str
    llm_model: str
    embedding_model: str
    total_chunks: int
