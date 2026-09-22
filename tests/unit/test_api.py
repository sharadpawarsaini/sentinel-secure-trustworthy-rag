"""Integration and unit tests for FastAPI endpoints (Component 2.7)."""

import io
import pytest
from fastapi.testclient import TestClient
from sentinel.backend.api import app, vector_store, generator
from sentinel.rag.generator import MockLLMClient


@pytest.fixture(scope="module")
def client():
    """TestClient configured with MockLLM for deterministic assertions."""
    # Ensure generator uses MockLLM for predictable tests
    generator.client = MockLLMClient(model_name="test-mock-llm")
    with TestClient(app) as test_client:
        yield test_client
    # Teardown
    vector_store.clear_collection()


def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "embedding_model" in data


def test_upload_and_query_flow(client: TestClient):
    # 1. Upload sample text document
    sample_content = (
        "Executive Leadership:\n"
        "The Chief Executive Officer is John Smith.\n"
        "The company was incorporated in 2015.\n"
        "Annual employee paid vacation leave is 25 days."
    )
    file_bytes = io.BytesIO(sample_content.encode("utf-8"))
    
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("corporate_facts.txt", file_bytes, "text/plain")}
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert upload_data["filename"] == "corporate_facts.txt"
    assert upload_data["chunks_created"] > 0
    assert upload_data["status"] == "indexed"

    # 2. Verify document in listing
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs_data = docs_res.json()
    assert docs_data["total_chunks"] > 0
    assert "corporate_facts.txt" in docs_data["unique_documents"]

    # 3. Query RAG for CEO
    query_res = client.post(
        "/api/rag/query",
        json={"query": "Who is the CEO of the company?", "top_k": 2}
    )
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert "John Smith" in query_data["answer"]
    assert len(query_data["retrieved_chunks"]) > 0
    assert query_data["retrieved_chunks"][0]["source_filename"] == "corporate_facts.txt"
    assert query_data["retrieved_chunks"][0]["similarity_score"] > 0.40
    assert query_data["pipeline_mode"] == "BASELINE_RAG"

    # 4. Delete document
    del_res = client.delete("/api/documents/corporate_facts.txt")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "deleted"
    assert del_data["deleted_chunks"] > 0


def test_upload_unsupported_format(client: TestClient):
    fake_exe = io.BytesIO(b"binary content")
    res = client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")}
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]


def test_empty_query(client: TestClient):
    res = client.post("/api/rag/query", json={"query": "   ", "top_k": 2})
    assert res.status_code == 400
