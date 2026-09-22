"""Central configuration and settings for SENTINEL."""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server configuration
    host: str = Field(default="127.0.0.1", alias="SENTINEL_HOST")
    port: int = Field(default=8000, alias="SENTINEL_PORT")
    debug: bool = Field(default=True, alias="SENTINEL_DEBUG")

    # LLM Backend selection: "ollama", "gemini", "openai", "mock"
    llm_provider: Literal["ollama", "gemini", "openai", "mock"] = Field(
        default="ollama", alias="LLM_PROVIDER"
    )
    llm_model: str = Field(default="codellama:latest", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Embedding model configuration
    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL_NAME"
    )
    vector_store_dir: Path = Field(
        default=Path("./data/vectorstore"), alias="VECTOR_STORE_DIR"
    )

    # Chunking hyperparameters
    default_chunk_size: int = 500
    default_chunk_overlap: int = 50

    # Trust and Security thresholds (for upcoming phases)
    trust_threshold_high: float = Field(default=0.75, alias="TRUST_THRESHOLD_HIGH")
    trust_threshold_low: float = Field(default=0.50, alias="TRUST_THRESHOLD_LOW")
    security_risk_threshold: float = Field(default=0.70, alias="SECURITY_RISK_THRESHOLD")


# Global settings singleton
settings = Settings()
