"""FastAPI REST application and endpoints for SENTINEL Baseline RAG.

Exposes endpoints for document upload, question querying, evidence inspection,
and collection management.
Owned by: Sharad (Backend Architecture & Integration)
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sentinel.config import settings
from sentinel.rag.document_loader import DocumentLoader
from sentinel.rag.chunker import TextChunker
from sentinel.rag.vector_store import VectorStoreManager
from sentinel.rag.generator import BaselineGenerator, get_llm_client
from sentinel.backend.schemas import (
    DocumentUploadResponse,
    QueryRequest,
    QueryResponse,
    ChunkEvidence,
    DocumentListResponse,
    HealthResponse
)

# Initialize FastAPI application
app = FastAPI(
    title="SENTINEL: Secure and Trustworthy RAG",
    description="Research-oriented Secure and Trustworthy RAG System - Phase 2 Baseline RAG",
    version="0.1.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Component singletons
chunker = TextChunker(
    chunk_size=settings.default_chunk_size,
    chunk_overlap=settings.default_chunk_overlap
)
vector_store = VectorStoreManager()
generator = BaselineGenerator(llm_client=get_llm_client())

# Static directory path
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the web portal dashboard."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index HTML not found.")
    return FileResponse(str(index_path))


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def healthcheck():
    """System health check and operational parameters."""
    stats = vector_store.get_collection_stats()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model_name,
        total_chunks=stats["total_chunks"]
    )


@app.post(
    "/api/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"]
)
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document into the ChromaDB vector store.

    Accepts .pdf, .docx, and .txt files.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a valid filename.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in DocumentLoader.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported formats: {DocumentLoader.SUPPORTED_EXTENSIONS}"
        )

    try:
        content = await file.read()
        loaded_doc = DocumentLoader.load_from_bytes(content, filename=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")

    # Chunk the extracted document
    chunks = chunker.chunk_document(loaded_doc)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document contained no chunkable text content.")

    # Upsert chunks into ChromaDB
    try:
        vector_store.add_chunks(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store document in vector database: {e}")

    return DocumentUploadResponse(
        filename=loaded_doc.source_filename,
        file_type=loaded_doc.file_type,
        character_count=loaded_doc.character_count,
        chunks_created=len(chunks),
        status="indexed"
    )


@app.get("/api/documents", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents():
    """List indexed documents and collection stats."""
    stats = vector_store.get_collection_stats()
    return DocumentListResponse(
        total_chunks=stats["total_chunks"],
        unique_documents_count=stats["unique_documents_count"],
        unique_documents=stats["unique_documents"],
        collection_name=stats["collection_name"]
    )


@app.delete("/api/documents/{filename}", tags=["Documents"])
async def delete_document(filename: str):
    """Delete a document and all its chunks from the vector store."""
    deleted_count = vector_store.delete_document(filename)
    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found in vector store."
        )
    return {
        "status": "deleted",
        "filename": filename,
        "deleted_chunks": deleted_count
    }


@app.post("/api/rag/query", response_model=QueryResponse, tags=["RAG"])
async def query_rag(request: QueryRequest):
    """Query the Baseline RAG system.

    Retrieves top-K semantic chunks from ChromaDB, constructs a grounded prompt,
    and returns the LLM response with verifiable evidence chunks.
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Semantic Retrieval
    retrieved_chunks = vector_store.query_similar(
        query_text=clean_query,
        top_k=request.top_k,
        score_threshold=request.score_threshold
    )

    # 2. Baseline Generation
    gen_result = generator.generate(query=clean_query, chunks=retrieved_chunks)

    # Convert to API response evidence format
    evidence_list = [
        ChunkEvidence(
            chunk_id=c.chunk_id,
            source_filename=c.source_filename,
            chunk_index=c.chunk_index,
            similarity_score=c.similarity_score,
            text=c.text,
            metadata=c.metadata
        )
        for c in retrieved_chunks
    ]

    return QueryResponse(
        query=gen_result.query,
        answer=gen_result.answer,
        retrieved_chunks=evidence_list,
        model=gen_result.model,
        provider=gen_result.provider,
        latency_ms=gen_result.latency_ms,
        pipeline_mode="BASELINE_RAG"
    )
