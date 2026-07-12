from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    # ── Provider Selection ────────────────────────────────────────────────────
    llm_provider: str = Field("gemini", alias="LLM_PROVIDER")

    # ── Gemini ───────────────────────────────────────────────────────────────
    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")

    # ── Groq (Fallback) ──────────────────────────────────────────────────────
    groq_api_key: str | None = Field(None, alias="GROQ_API_KEY")
    groq_model: str = Field("llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # ── OpenAI (Future) ──────────────────────────────────────────────────────
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")

    # ── Azure OpenAI (Future) ────────────────────────────────────────────────
    azure_openai_key: str | None = Field(None, alias="AZURE_OPENAI_KEY")
    azure_openai_endpoint: str | None = Field(None, alias="AZURE_OPENAI_ENDPOINT")

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = Field("BAAI/bge-m3", alias="EMBEDDING_MODEL")
    reranker_model: str = Field("BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")

    model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}
