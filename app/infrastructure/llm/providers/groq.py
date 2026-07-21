"""llm/providers/groq.py — Groq provider (ultra-fast Llama inference)."""

import time

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.llm.providers.base import BaseLLMProvider, LLMResponse

log = get_logger("llm.groq")


class GroqProvider(BaseLLMProvider):
    """Groq Cloud provider using the official groq SDK."""

    def __init__(self) -> None:
        self._client = None

    def _init(self) -> None:
        if self._client is not None:
            return
        try:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=settings.llm.groq_api_key)
            log.info(f"Groq provider initialized (model={self.model})")
        except Exception as exc:
            log.error(f"Failed to initialize Groq: {exc}")
            raise

    @property
    def name(self) -> str:
        return "groq"

    @property
    def model(self) -> str:
        return settings.llm.groq_model

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        self._init()
        start = time.perf_counter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or settings.llm.temperature,
                max_tokens=max_tokens or settings.llm.max_tokens,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            choice = response.choices[0]
            usage = response.usage
            return LLMResponse(
                text=choice.message.content or "",
                provider=self.name,
                model=self.model,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            log.error(f"Groq generate failed: {exc}")
            raise

    async def is_available(self) -> bool:
        return bool(settings.llm.groq_api_key)
