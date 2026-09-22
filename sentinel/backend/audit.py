"""In-memory telemetry and query activity audit logger for SENTINEL Admin Console.

Tracks real-time query events, latency profiles, document ingestions, and vector store metrics.
Owned by: Sharad (System Integration & Observability)
"""

from collections import deque
from datetime import datetime, timezone
import threading
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryAuditRecord(BaseModel):
    """Detailed record of a single RAG query transaction."""
    id: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    query: str
    top_k: int
    provider: str
    model: str
    latency_ms: float
    chunks_count: int
    top_similarity_score: float
    answer: str
    retrieved_chunks_preview: List[Dict[str, Any]] = Field(default_factory=list)


class IngestionAuditRecord(BaseModel):
    """Record of an ingested document event."""
    filename: str
    file_type: str
    character_count: int
    chunks_created: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ActivityLogger:
    """Thread-safe circular buffer telemetry logger for admin observability."""

    _instance: Optional["ActivityLogger"] = None
    _lock = threading.Lock()

    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self.queries: deque[QueryAuditRecord] = deque(maxlen=max_records)
        self.ingestions: deque[IngestionAuditRecord] = deque(maxlen=max_records)
        self._counter = 0

    @classmethod
    def get_instance(cls) -> "ActivityLogger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def log_query(
        self,
        query: str,
        top_k: int,
        provider: str,
        model: str,
        latency_ms: float,
        chunks_count: int,
        top_similarity_score: float,
        answer: str,
        retrieved_chunks: Optional[List[Any]] = None
    ) -> QueryAuditRecord:
        """Log a new RAG query event into the circular buffer."""
        with self._lock:
            self._counter += 1
            chunks_summary = []
            if retrieved_chunks:
                for c in retrieved_chunks:
                    if hasattr(c, "chunk_id"):
                        cid = str(c.chunk_id)
                        sfn = str(getattr(c, "source_filename", ""))
                        cidx = int(getattr(c, "chunk_index", 0))
                        sim = float(getattr(c, "similarity_score", 0.0))
                        txt = str(getattr(c, "text", ""))[:120] + "..."
                    elif isinstance(c, dict):
                        cid = str(c.get("chunk_id", ""))
                        sfn = str(c.get("source_filename", ""))
                        cidx = int(c.get("chunk_index", 0))
                        sim = float(c.get("similarity_score", 0.0))
                        txt = str(c.get("text", ""))[:120] + "..."
                    else:
                        cid = ""
                        sfn = ""
                        cidx = 0
                        sim = 0.0
                        txt = str(c)[:120] + "..."

                    chunks_summary.append({
                        "chunk_id": cid,
                        "source_filename": sfn,
                        "chunk_index": cidx,
                        "similarity_score": sim,
                        "text_snippet": txt
                    })

            record = QueryAuditRecord(
                id=self._counter,
                query=query,
                top_k=top_k,
                provider=provider,
                model=model,
                latency_ms=round(latency_ms, 2),
                chunks_count=chunks_count,
                top_similarity_score=round(top_similarity_score, 4),
                answer=answer,
                retrieved_chunks_preview=chunks_summary
            )
            self.queries.appendleft(record)
            return record

    def log_ingestion(
        self,
        filename: str,
        file_type: str,
        character_count: int,
        chunks_created: int
    ) -> IngestionAuditRecord:
        """Log a document ingestion event."""
        with self._lock:
            record = IngestionAuditRecord(
                filename=filename,
                file_type=file_type,
                character_count=character_count,
                chunks_created=chunks_created
            )
            self.ingestions.appendleft(record)
            return record

    def get_queries(self, limit: int = 50) -> List[QueryAuditRecord]:
        """Get recent query records."""
        with self._lock:
            return list(self.queries)[:limit]

    def get_ingestions(self, limit: int = 50) -> List[IngestionAuditRecord]:
        """Get recent document ingestion records."""
        with self._lock:
            return list(self.ingestions)[:limit]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Compute aggregate performance metrics."""
        with self._lock:
            total_queries = len(self.queries)
            if total_queries == 0:
                avg_latency = 0.0
                max_latency = 0.0
                min_latency = 0.0
            else:
                latencies = [q.latency_ms for q in self.queries]
                avg_latency = round(sum(latencies) / total_queries, 2)
                max_latency = round(max(latencies), 2)
                min_latency = round(min(latencies), 2)

            return {
                "total_queries_logged": self._counter,
                "current_buffer_queries": total_queries,
                "average_latency_ms": avg_latency,
                "max_latency_ms": max_latency,
                "min_latency_ms": min_latency,
                "total_ingestions_logged": len(self.ingestions)
            }

    def clear_logs(self) -> None:
        """Reset query and ingestion audit records."""
        with self._lock:
            self.queries.clear()
            self.ingestions.clear()


# Global logger instance
activity_logger = ActivityLogger.get_instance()
