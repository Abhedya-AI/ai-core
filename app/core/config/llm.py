from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._base import _ENV_FILES


class LLMSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="LLM_",          # Improvement 1: env_prefix for LLM_ vars
        env_file=_ENV_FILES,        # Improvement 2: dynamic env file
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,      # allow alias AND field name
    )

    provider: Literal["gemini", "groq", "openai", "azure"] = Field(default="gemini")
    temperature: float = Field(default=0.2)
    max_tokens: int = Field(default=4096)

    # API keys break from the LLM_ prefix intentionally —
    # they follow provider naming conventions (GEMINI_API_KEY, not LLM_GEMINI_API_KEY)
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Model selection per provider
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Embedding and reranking
    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")

    @property
    def active_api_key(self) -> str:
        """Return the API key for the currently selected provider."""
        return {
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
            "openai": self.openai_api_key,
        }.get(self.provider, "")

    @property
    def active_model(self) -> str:
        """Return the model name for the currently selected provider."""
        return {
            "gemini": self.gemini_model,
            "groq": self.groq_model,
        }.get(self.provider, self.gemini_model)
