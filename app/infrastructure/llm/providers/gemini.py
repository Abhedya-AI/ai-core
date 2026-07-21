"""llm/providers/gemini.py — Google Gemini provider."""

import time

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.llm.providers.base import BaseLLMProvider, LLMResponse

log = get_logger("llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider using the google-genai SDK."""

    def __init__(self) -> None:
        self._client = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        try:
            import google.genai as genai
            self._client = genai.Client(api_key=settings.llm.gemini_api_key)
            self._initialized = True
            log.info(f"Gemini provider initialized (model={self.model})")
        except Exception as exc:
            log.error(f"Failed to initialize Gemini: {exc}")
            raise

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return settings.llm.gemini_model

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        self._init()
        start = time.perf_counter()
        try:
            import asyncio
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=temperature or settings.llm.temperature,
                max_output_tokens=max_tokens or settings.llm.max_tokens,
                system_instruction=system_prompt,
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                ),
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            text = response.text or ""
            usage = response.usage_metadata
            return LLMResponse(
                text=text,
                provider=self.name,
                model=self.model,
                input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            log.error(f"Gemini generate failed: {exc}")
            raise

    async def is_available(self) -> bool:
        return bool(settings.llm.gemini_api_key)
