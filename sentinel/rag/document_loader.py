"""Document ingestion and multi-format text extraction for SENTINEL.

Handles extraction of raw text and metadata from PDF, DOCX, and TXT files.
Owned by: Bhumika (RAG Foundation)
"""

from datetime import datetime, timezone
import io
from pathlib import Path
from typing import BinaryIO, Dict, Any, Union
import docx
from pydantic import BaseModel, Field
import pypdf


class LoadedDocument(BaseModel):
    """Structured representation of an extracted document."""
    text: str = Field(..., description="Extracted and cleaned plain text content.")
    source_filename: str = Field(..., description="Original filename.")
    file_type: str = Field(..., description="File extension / format (.pdf, .docx, .txt).")
    character_count: int = Field(..., description="Total character count.")
    page_count: int = Field(default=1, description="Total pages (1 for non-paginated files).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document metadata.")
    ingested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of ingestion."
    )


class DocumentLoader:
    """Multi-format document loader supporting .pdf, .docx, and .txt files."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> LoadedDocument:
        """Load and extract text from a file on disk.

        Args:
            file_path: Path to the target file.

        Returns:
            LoadedDocument instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or the file is empty.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found at: {path}")

        suffix = path.suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{suffix}'. Supported formats: {cls.SUPPORTED_EXTENSIONS}"
            )

        with open(path, "rb") as f:
            return cls.load_from_bytes(f.read(), filename=path.name)

    @classmethod
    def load_from_bytes(cls, file_bytes: bytes, filename: str) -> LoadedDocument:
        """Load and extract text from in-memory bytes (e.g. from web upload).

        Args:
            file_bytes: Raw binary content of the file.
            filename: Original filename to infer type.

        Returns:
            LoadedDocument instance.

        Raises:
            ValueError: If empty, corrupt, or unsupported.
        """
        if not file_bytes:
            raise ValueError(f"Uploaded file '{filename}' is empty (0 bytes).")

        suffix = Path(filename).suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{suffix}' for '{filename}'. "
                f"Supported: {cls.SUPPORTED_EXTENSIONS}"
            )

        stream = io.BytesIO(file_bytes)

        if suffix == ".txt":
            return cls._load_txt(stream, filename)
        elif suffix == ".pdf":
            return cls._load_pdf(stream, filename)
        elif suffix == ".docx":
            return cls._load_docx(stream, filename)
        else:
            raise ValueError(f"No parser available for {suffix}")

    @classmethod
    def _clean_text(cls, raw_text: str) -> str:
        """Normalize line breaks and strip non-standard control characters."""
        if not raw_text:
            return ""
        # Standardize carriage returns
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace non-breaking spaces
        text = text.replace("\xa0", " ")
        # Remove null bytes
        text = text.replace("\x00", "")
        return text.strip()

    @classmethod
    def _load_txt(cls, stream: BinaryIO, filename: str) -> LoadedDocument:
        """Extract text from plain text stream with encoding fallback."""
        raw_bytes = stream.read()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("latin-1")
            except Exception as e:
                raise ValueError(f"Failed to decode text file '{filename}': {e}") from e

        cleaned_text = cls._clean_text(text)
        if not cleaned_text:
            raise ValueError(f"Text file '{filename}' contains no readable text.")

        return LoadedDocument(
            text=cleaned_text,
            source_filename=filename,
            file_type=".txt",
            character_count=len(cleaned_text),
            page_count=1,
            metadata={"encoding": "utf-8/latin-1"}
        )

    @classmethod
    def _load_pdf(cls, stream: BinaryIO, filename: str) -> LoadedDocument:
        """Extract text and page counts from PDF stream using pypdf."""
        try:
            reader = pypdf.PdfReader(stream)
        except Exception as e:
            raise ValueError(f"Corrupt or invalid PDF file '{filename}': {e}") from e

        pages_text = []
        page_count = len(reader.pages)
        for idx, page in enumerate(reader.pages):
            page_str = page.extract_text() or ""
            pages_text.append(page_str)

        full_text = cls._clean_text("\n\n".join(pages_text))
        if not full_text:
            raise ValueError(
                f"PDF file '{filename}' contains no extractable text (it may be scanned/rasterized)."
            )

        return LoadedDocument(
            text=full_text,
            source_filename=filename,
            file_type=".pdf",
            character_count=len(full_text),
            page_count=page_count,
            metadata={"page_count": page_count}
        )

    @classmethod
    def _load_docx(cls, stream: BinaryIO, filename: str) -> LoadedDocument:
        """Extract paragraphs and table text from DOCX stream."""
        try:
            doc = docx.Document(stream)
        except Exception as e:
            raise ValueError(f"Corrupt or invalid DOCX file '{filename}': {e}") from e

        content_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                content_parts.append(para.text)

        # Extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    content_parts.append(row_text)

        full_text = cls._clean_text("\n\n".join(content_parts))
        if not full_text:
            raise ValueError(f"DOCX file '{filename}' contains no extractable text.")

        return LoadedDocument(
            text=full_text,
            source_filename=filename,
            file_type=".docx",
            character_count=len(full_text),
            page_count=1,
            metadata={"paragraph_count": len(doc.paragraphs)}
        )
