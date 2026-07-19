"""
llm.py — LLM provider and embedding settings.

Responsibility: API keys, model names, generation parameters, and embedding
configuration for all supported LLM providers.

Provider abstraction rule:
  Every module calls  llm.generate(prompt)
  The LLM Gateway reads  settings.llm.provider  to route the call.
  Switching providers = changing one env var.  Not one line of code.

Supported providers: gemini | groq | openai | azure
"""

from typing import Literal

from pydantic import Field, model_validator

from app.core.config._base import _BaseConfig

LLMProvider = Literal["gemini", "groq", "openai", "azure"]


class LLMSettings(_BaseConfig):
    """LLM provider configuration and generation defaults."""

    # ── Provider selection ────────────────────────────────────────────────────
    provider: LLMProvider = Field(
        default="gemini",
        alias="LLM_PROVIDER",
        description="Active LLM provider: gemini | groq | openai | azure.",
    )

    # ── Gemini (Primary) ─────────────────────────────────────────────────────
    gemini_api_key: str | None = Field(
        default=None,
        alias="GEMINI_API_KEY",
        description="Google Gemini API key.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        alias="GEMINI_MODEL",
        description="Gemini model identifier.",
    )
    gemini_temperature: float = Field(
        default=0.1,
        alias="GEMINI_TEMPERATURE",
        ge=0.0,
        le=2.0,
        description="Gemini sampling temperature.",
    )

    # ── Groq (Fallback) ──────────────────────────────────────────────────────
    groq_api_key: str | None = Field(
        default=None,
        alias="GROQ_API_KEY",
        description="Groq API key.",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_MODEL",
        description="Groq model identifier.",
    )

    # ── OpenAI (Future) ──────────────────────────────────────────────────────
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key.",
    )
    openai_model: str = Field(
        default="gpt-4o",
        alias="OPENAI_MODEL",
        description="OpenAI model identifier.",
    )

    # ── Azure OpenAI (Future) ────────────────────────────────────────────────
    azure_openai_key: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_KEY",
        description="Azure OpenAI API key.",
    )
    azure_openai_endpoint: str | None = Field(
        default=None,
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL.",
    )
    azure_openai_model: str = Field(
        default="gpt-4o",
        alias="AZURE_OPENAI_MODEL",
        description="Azure OpenAI deployment name.",
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        alias="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version string.",
    )

    # ── Generation defaults ───────────────────────────────────────────────────
    max_tokens: int = Field(
        default=8192,
        alias="LLM_MAX_TOKENS",
        description="Default maximum tokens for generation.",
    )
    temperature: float = Field(
        default=0.1,
        alias="LLM_TEMPERATURE",
        ge=0.0,
        le=2.0,
        description="Default sampling temperature.",
    )
    request_timeout: int = Field(
        default=60,
        alias="LLM_REQUEST_TIMEOUT",
        description="LLM API request timeout in seconds.",
    )
    max_retries: int = Field(
        default=3,
        alias="LLM_MAX_RETRIES",
        description="Number of retries on transient API failures.",
    )

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="BAAI/bge-m3",
        alias="EMBEDDING_MODEL",
        description="HuggingFace embedding model name.",
    )
    reranker_model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        alias="RERANKER_MODEL",
        description="HuggingFace reranker model name.",
    )
    embedding_batch_size: int = Field(
        default=32,
        alias="EMBEDDING_BATCH_SIZE",
        description="Batch size for embedding inference.",
    )
    embedding_device: str = Field(
        default="cpu",
        alias="EMBEDDING_DEVICE",
        description="Device for embedding model: cpu | cuda | mps.",
    )

    # ── Derived helpers ───────────────────────────────────────────────────────

    @property
    def active_api_key(self) -> str | None:
        """Return the API key for the currently active provider."""
        key_map: dict[str, str | None] = {
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
            "openai": self.openai_api_key,
            "azure": self.azure_openai_key,
        }
        return key_map.get(self.provider)

    @property
    def active_model(self) -> str:
        """Return the model name for the currently active provider."""
        model_map: dict[str, str] = {
            "gemini": self.gemini_model,
            "groq": self.groq_model,
            "openai": self.openai_model,
            "azure": self.azure_openai_model,
        }
        return model_map.get(self.provider, self.gemini_model)

    # ── Validation ────────────────────────────────────────────────────────────

    @model_validator(mode="after")
    def _warn_missing_api_key(self) -> "LLMSettings":
        """Warn (not fail) if the active provider has no API key configured."""
        import warnings
        if self.active_api_key is None:
            warnings.warn(
                f"LLM provider '{self.provider}' has no API key set. "
                f"Set {self.provider.upper()}_API_KEY in your .env file.",
                stacklevel=2,
            )
        return self
