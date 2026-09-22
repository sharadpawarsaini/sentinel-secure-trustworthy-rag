"""Baseline generation engine and LLM client interfaces for SENTINEL.

Handles evidence prompt compilation and structured generation across LLM backends
(Ollama, Mock for reproducible testing, and OpenAI-compatible endpoints).
Owned by: Bhumika (RAG Foundation)
"""

import abc
import time
from typing import List, Optional, Dict, Any
import requests
from pydantic import BaseModel, Field

from sentinel.config import settings
from sentinel.rag.vector_store import RetrievedChunk


class GenerationResult(BaseModel):
    """Structured output returned by the generation engine."""
    query: str = Field(..., description="Original user query.")
    answer: str = Field(..., description="Generated answer text.")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Evidence chunks provided.")
    formatted_prompt: str = Field(..., description="Complete prompt text sent to LLM.")
    model: str = Field(..., description="Model identifier used for generation.")
    provider: str = Field(..., description="Backend provider ('ollama', 'mock', 'openai').")
    latency_ms: float = Field(..., description="Total roundtrip generation latency in milliseconds.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata.")


class BaseLLMClient(abc.ABC):
    """Abstract interface for LLM completion providers."""

    @abc.abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text completion for the provided prompt."""
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier."""
        pass

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """Return model identifier."""
        pass


class MockLLMClient(BaseLLMClient):
    """Deterministic mock LLM for offline unit testing and automated benchmarks."""

    def __init__(self, model_name: str = "sentinel-mock-v1"):
        self._model = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate deterministic responses for testing."""
        # Check if context was provided
        if "Context Information:\nNone" in prompt or "No relevant evidence" in prompt:
            return "I do not have sufficient information in the provided context to answer this question."

        # If question asks about CEO
        if "CEO" in prompt or "chief executive" in prompt.lower():
            if "John Smith" in prompt:
                return "Based on the provided context, the CEO is John Smith."
            return "The context does not state who the CEO is."

        # If question asks about annual vacation
        if "vacation" in prompt.lower() or "leave" in prompt.lower():
            if "25 days" in prompt:
                return "Employees receive 25 days of annual paid vacation leave."

        # Generic grounded synthesis for test scenarios
        return "Based strictly on the provided context, the requested information is verified."


class OllamaClient(BaseLLMClient):
    """Local Ollama client connecting to local daemon (e.g. llama3:8b)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: int = 60
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to communicate with local Ollama at {self.base_url}: {e}. "
                "Ensure Ollama is running (`ollama serve`), or switch LLM_PROVIDER=mock."
            ) from e


class OpenAICompatibleClient(BaseLLMClient):
    """Generic OpenAI/Gemini REST client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key or settings.openai_api_key or settings.gemini_api_key
        self._model = model or "gpt-4o-mini"
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("API key must be configured in .env for OpenAI/Gemini provider.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            url,
            headers=headers,
            json={"model": self._model, "messages": messages, "temperature": 0.0},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> BaseLLMClient:
    """Factory creating the appropriate LLM client."""
    selected_provider = (provider or settings.llm_provider).lower()
    if selected_provider == "mock":
        return MockLLMClient(model_name=model or "sentinel-mock-v1")
    elif selected_provider == "ollama":
        return OllamaClient(model=model)
    elif selected_provider in ("openai", "gemini"):
        return OpenAICompatibleClient(model=model)
    else:
        raise ValueError(f"Unknown LLM provider '{selected_provider}'. Options: mock, ollama, openai, gemini.")


class BaselineGenerator:
    """Standard Baseline RAG Generation Engine."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful and strictly factual AI assistant for the SENTINEL system.\n"
        "Answer the user's question based strictly on the retrieved context provided below.\n"
        "If the context does not provide sufficient evidence to answer the question, state:\n"
        "'I do not have sufficient information in the provided context to answer this question.'\n"
        "Do not speculate, assume, or extrapolate beyond the facts directly provided."
    )

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize the generator.

        Args:
            llm_client: Backend LLM client. Defaults to settings-configured client.
            system_prompt: System instructions guiding the LLM.
        """
        self.client = llm_client or get_llm_client()
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks into structured context blocks."""
        if not chunks:
            return "None (No relevant evidence retrieved)."

        formatted_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"[Source {i}: {chunk.source_filename}, Chunk {chunk.chunk_index} | Sim: {chunk.similarity_score}]"
            formatted_parts.append(f"{source_info}\n{chunk.text.strip()}")

        return "\n\n".join(formatted_parts)

    def build_prompt(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """Compile context and user query into the final prompt."""
        context_str = self.format_context(chunks)
        return (
            f"Context Information:\n{context_str}\n\n"
            f"User Question:\n{query.strip()}\n\n"
            f"Answer:"
        )

    def generate(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate a grounded answer conditioned on retrieved chunks.

        Args:
            query: User's question.
            chunks: List of retrieved evidence chunks.
            system_prompt: Optional override for system instructions.

        Returns:
            GenerationResult instance.
        """
        prompt = self.build_prompt(query, chunks)
        sys_prompt = system_prompt or self.system_prompt

        start_time = time.perf_counter()
        answer = self.client.complete(prompt=prompt, system_prompt=sys_prompt)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return GenerationResult(
            query=query,
            answer=answer,
            retrieved_chunks=chunks,
            formatted_prompt=prompt,
            model=self.client.model_name,
            provider=self.client.provider_name,
            latency_ms=round(elapsed_ms, 2),
            metadata={"chunks_count": len(chunks)}
        )
