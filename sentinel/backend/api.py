"""FastAPI REST application and endpoints for SENTINEL.

Exposes endpoints for document upload, question querying with closed-loop security
and trust evaluation, collection management, and admin observability.
Owned by: Sharad (Lead AI Engineer & System Architect)
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
from sentinel.security.document_scanner import DocumentScanner
from sentinel.pipeline import SentinelPipeline
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
    description="Research-oriented Secure and Trustworthy RAG System - Phase 4 Integrated Pipeline",
    version="0.4.0"
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
document_scanner = DocumentScanner()
pipeline = SentinelPipeline(
    vector_store=vector_store,
    generator=generator
)

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
        version="0.4.0",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model_name,
        total_chunks=stats["total_chunks"],
        pipeline_phase="Phase 4: Trust Evaluation & Hallucination Mitigation"
    )


@app.post(
    "/api/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"]
)
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document into the ChromaDB vector store.

    Accepts .pdf, .docx, and .txt files. Runs document poisoning inspection
    and quarantines malicious chunks automatically.
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

    # 1. Chunk the extracted document
    chunks = chunker.chunk_document(loaded_doc)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document contained no chunkable text content.")

    # 2. Security scan for poisoning and canary injections
    scan_report = document_scanner.scan_document(chunks, filename=loaded_doc.source_filename)

    # 3. Upsert chunks into ChromaDB
    try:
        vector_store.add_chunks(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store document in vector database: {e}")

    # 4. Telemetry logging
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
        quarantined_chunks=scan_report.quarantined_chunks_count,
        status="indexed" if scan_report.quarantined_chunks_count == 0 else "indexed_with_quarantines"
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
    """Query the SENTINEL Trust-Aware RAG system.

    Executes closed-loop pipeline:
    Input Security -> Vector Retrieval -> Context Security -> LLM Generation
    -> Trust Scoring -> Mitigation -> Egress Scan -> Verifiable Response.
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Override LLM provider if requested
    active_pipeline = pipeline
    if request.provider:
        custom_gen = BaselineGenerator(llm_client=get_llm_client(provider=request.provider))
        active_pipeline = SentinelPipeline(
            vector_store=vector_store,
            generator=custom_gen
        )

    # Execute full multi-barrier pipeline
    try:
        pipeline_res = active_pipeline.query(
            query_text=clean_query,
            top_k=request.top_k,
            enable_mitigation=request.enable_mitigation
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline processing failure: {e}"
        )

    # Convert retrieved chunks to API schema
    evidence_list = [
        ChunkEvidence(
            chunk_id=c.chunk_id,
            source_filename=c.source_filename,
            chunk_index=c.chunk_index,
            similarity_score=c.similarity_score,
            text=c.text,
            metadata=c.metadata
        )
        for c in pipeline_res.retrieved_chunks
    ]

    # Telemetry logging for Admin Observability
    top_sim = pipeline_res.retrieved_chunks[0].similarity_score if pipeline_res.retrieved_chunks else 0.0
    activity_logger.log_query(
        query=clean_query,
        top_k=request.top_k,
        provider=generator.client.provider_name,
        model=generator.client.model_name,
        latency_ms=pipeline_res.telemetry.total_latency_ms,
        chunks_count=len(pipeline_res.retrieved_chunks),
        top_similarity_score=top_sim,
        answer=pipeline_res.answer,
        retrieved_chunks=pipeline_res.retrieved_chunks
    )

    return QueryResponse(
        query=pipeline_res.query,
        answer=pipeline_res.answer,
        retrieved_chunks=evidence_list,
        model=generator.client.model_name,
        provider=generator.client.provider_name,
        latency_ms=pipeline_res.telemetry.total_latency_ms,
        pipeline_mode="SENTINEL_CLOSED_LOOP",
        trust_score=pipeline_res.trust_score,
        trust_verdict=pipeline_res.trust_verdict,
        is_abstained=pipeline_res.is_abstained,
        abstention_reason=pipeline_res.abstention_reason,
        security_action=pipeline_res.security_action,
        quarantined_chunks_count=pipeline_res.quarantined_chunks_count,
        telemetry=pipeline_res.telemetry.model_dump()
    )


# --- Admin Observability Endpoints ---

@app.get("/api/admin/stats", response_model=AdminStatsResponse, tags=["Admin"])
async def get_admin_stats():
    """Retrieve aggregate telemetry and operational health metrics."""
    vs_stats = vector_store.get_collection_stats()
    metrics = activity_logger.get_metrics_summary()

    return AdminStatsResponse(
        status="operational",
        pipeline_phase="Phase 4: Trust & Security Integrated",
        system_version="0.4.0",
        active_llm_provider=settings.llm_provider,
        active_llm_model=generator.client.model_name,
        embedding_model=settings.embedding_model_name,
        embedding_dimension=vector_store.embedder.dimension,
        vector_store_path=str(settings.vector_store_dir),
        vector_store_collection=vector_store.collection_name,
        total_chunks_indexed=vs_stats["total_chunks"],
        total_unique_documents=vs_stats["unique_documents_count"],
        total_queries_logged=metrics["total_queries"],
        average_latency_ms=metrics["avg_latency_ms"],
        min_latency_ms=metrics["min_latency_ms"],
        max_latency_ms=metrics["max_latency_ms"]
    )


@app.get("/api/admin/chunks", response_model=AdminChunksResponse, tags=["Admin"])
async def list_admin_chunks(
    doc: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Retrieve indexed chunks with metadata for inspection and debugging."""
    all_chunks = vector_store.get_all_chunks(limit=500)

    if doc:
        filtered = [c for c in all_chunks if c.source_filename == doc]
    else:
        filtered = all_chunks

    paginated = filtered[offset: offset + limit]

    chunk_items = [
        AdminChunkItem(
            chunk_id=c.chunk_id,
            source_filename=c.source_filename,
            chunk_index=c.chunk_index,
            character_count=c.character_count,
            start_char=c.start_char,
            end_char=c.end_char,
            text=c.text,
            metadata=c.metadata
        )
        for c in paginated
    ]

    return AdminChunksResponse(
        total_chunks=len(all_chunks),
        filtered_count=len(filtered),
        chunks=chunk_items
    )


@app.get("/api/admin/activity", tags=["Admin"])
async def get_activity_feed(limit: int = 50):
    """Retrieve recent queries and document ingestion events for the live log."""
    return {
        "recent_queries": activity_logger.get_recent_queries(limit=limit),
        "recent_ingestions": activity_logger.get_recent_ingestions(limit=limit)
    }


@app.post("/api/admin/clear-data", tags=["Admin"])
async def clear_all_data():
    """Clear the persistent ChromaDB collection and flush telemetry logs."""
    vector_store.clear_collection()
    activity_logger.clear_all()
    return {
        "status": "cleared",
        "message": "Persistent vector store collection and telemetry logs have been reset."
    }
