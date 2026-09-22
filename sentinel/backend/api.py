"""FastAPI REST application and endpoints for SENTINEL Baseline RAG.

Exposes endpoints for document upload, question querying, evidence inspection,
and collection management.
Owned by: Sharad (Backend Architecture & Integration)
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sentinel.config import settings
from sentinel.rag.document_loader import DocumentLoader
from sentinel.rag.chunker import TextChunker
from sentinel.rag.vector_store import VectorStoreManager
from sentinel.rag.generator import BaselineGenerator, get_llm_client
from sentinel.backend.audit import activity_logger
from sentinel.backend.schemas import (
    DocumentUploadResponse,
    QueryRequest,
    QueryResponse,
    ChunkEvidence,
    DocumentListResponse,
    HealthResponse,
    AdminStatsResponse,
    AdminChunkItem,
    AdminChunksResponse
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Inline SVG favicon to prevent 404 browser noise."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<rect width="100" height="100" rx="20" fill="#0ea5e9"/>'
        '<path d="M50 20 L80 35 L80 60 C80 75 50 85 50 85 C50 85 20 75 20 60 L20 35 Z" fill="#0c4a6e" stroke="#ffffff" stroke-width="4"/>'
        '</svg>'
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the web portal dashboard."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index HTML not found.")
    return FileResponse(str(index_path))


@app.get("/admin", include_in_schema=False)
async def serve_admin():
    """Serve the Admin Observability Console."""
    admin_path = STATIC_DIR / "admin.html"
    if not admin_path.exists():
        raise HTTPException(status_code=404, detail="Admin HTML not found.")
    return FileResponse(str(admin_path))


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

    # Telemetry logging
    activity_logger.log_ingestion(
        filename=loaded_doc.source_filename,
        file_type=loaded_doc.file_type,
        character_count=loaded_doc.character_count,
        chunks_created=len(chunks)
    )

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
    try:
        active_generator = (
            BaselineGenerator(llm_client=get_llm_client(provider=request.provider))
            if request.provider
            else generator
        )
        gen_result = active_generator.generate(query=clean_query, chunks=retrieved_chunks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Generation failure: {e}"
        )

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

    # Telemetry logging for Admin Observability
    top_sim = retrieved_chunks[0].similarity_score if retrieved_chunks else 0.0
    activity_logger.log_query(
        query=clean_query,
        top_k=request.top_k,
        provider=gen_result.provider,
        model=gen_result.model,
        latency_ms=gen_result.latency_ms,
        chunks_count=len(retrieved_chunks),
        top_similarity_score=top_sim,
        answer=gen_result.answer,
        retrieved_chunks=retrieved_chunks
    )

    return QueryResponse(
        query=gen_result.query,
        answer=gen_result.answer,
        retrieved_chunks=evidence_list,
        model=gen_result.model,
        provider=gen_result.provider,
        latency_ms=gen_result.latency_ms,
        pipeline_mode="BASELINE_RAG"
    )


# --- Admin Observability Endpoints ---

@app.get("/api/admin/stats", response_model=AdminStatsResponse, tags=["Admin"])
async def get_admin_stats():
    """Retrieve aggregate telemetry and operational health metrics."""
    vs_stats = vector_store.get_collection_stats()
    metrics = activity_logger.get_metrics_summary()

    return AdminStatsResponse(
        status="operational",
        pipeline_phase="Phase 2: Baseline RAG",
        system_version="0.1.0",
        active_llm_provider=settings.llm_provider,
        active_llm_model=generator.client.model_name,
        embedding_model=settings.embedding_model_name,
        embedding_dimension=vector_store.embedder.dimension,
        vector_store_path=str(settings.vector_store_dir),
        vector_store_collection=vector_store.collection_name,
        total_chunks_indexed=vs_stats["total_chunks"],
        total_unique_documents=vs_stats["unique_documents_count"],
        total_queries_logged=metrics["total_queries_logged"],
        average_latency_ms=metrics["average_latency_ms"],
        min_latency_ms=metrics["min_latency_ms"],
        max_latency_ms=metrics["max_latency_ms"]
    )


@app.get("/api/admin/queries", tags=["Admin"])
async def get_admin_queries(limit: int = 100):
    """Retrieve recent query audit logs."""
    return activity_logger.get_queries(limit=limit)


@app.get("/api/admin/chunks", response_model=AdminChunksResponse, tags=["Admin"])
async def get_admin_chunks(source_filename: Optional[str] = None):
    """Inspect stored chunks directly from the ChromaDB vector index."""
    total_count = vector_store.collection.count()
    if total_count == 0:
        return AdminChunksResponse(total_chunks=0, filtered_count=0, chunks=[])

    where_filter = {"source_filename": source_filename} if source_filename else None
    results = vector_store.collection.get(
        where=where_filter,
        include=["documents", "metadatas"]
    )

    ids = results.get("ids", [])
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])

    chunk_items = []
    for chunk_id, doc_text, meta in zip(ids, docs, metas):
        meta_dict = meta or {}
        chunk_items.append(
            AdminChunkItem(
                chunk_id=chunk_id,
                source_filename=str(meta_dict.get("source_filename", "unknown")),
                chunk_index=int(meta_dict.get("chunk_index", 0)),
                character_count=int(meta_dict.get("character_count", len(doc_text))),
                start_char=int(meta_dict.get("start_char", 0)),
                end_char=int(meta_dict.get("end_char", len(doc_text))),
                text=doc_text,
                metadata=meta_dict
            )
        )

    # Sort chunks by source_filename then chunk_index
    chunk_items.sort(key=lambda x: (x.source_filename, x.chunk_index))

    return AdminChunksResponse(
        total_chunks=total_count,
        filtered_count=len(chunk_items),
        chunks=chunk_items
    )


@app.post("/api/admin/clear-logs", tags=["Admin"])
async def clear_admin_logs():
    """Reset the query audit trail buffer."""
    activity_logger.clear_logs()
    return {"status": "cleared"}
