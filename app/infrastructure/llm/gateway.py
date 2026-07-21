"""
llm/gateway.py — LLMGateway: the only LLM entry point.

No module outside llm/ should import a provider directly.
Everyone calls LLMGateway.generate().

The gateway:
  - Routes to the active provider from settings
  - Handles provider fallback on error
  - Logs latency, tokens, and provider used

Usage:
    from app.infrastructure.llm.gateway import LLMGateway

    llm = LLMGateway.get()
    response = await llm.generate(
        prompt="Explain the risk at sensor S-001",
        system_prompt="You are an industrial safety AI.",
    )
    print(response.text)
"""

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.llm.providers.base import BaseLLMProvider, LLMResponse
from app.infrastructure.llm.providers.gemini import GeminiProvider
from app.infrastructure.llm.providers.groq import GroqProvider

log = get_logger("llm.gateway")

_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


class LLMGateway:
    """
    LLM provider router and singleton.

    Selects the active provider from settings.llm.provider.
    Falls back to the alternative provider if the primary fails.
    """

    _instance: "LLMGateway | None" = None

    def __init__(self) -> None:
        self._primary: BaseLLMProvider = self._build_provider(settings.llm.provider)
        self._fallback: BaseLLMProvider | None = self._build_fallback()

    @classmethod
    def get(cls) -> "LLMGateway":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_provider(self, name: str) -> BaseLLMProvider:
        provider_cls = _PROVIDERS.get(name)
        if not provider_cls:
            raise ValueError(
                f"Unknown LLM provider: {name!r}. Choose from: {list(_PROVIDERS)}"
            )
        return provider_cls()

    def _build_fallback(self) -> BaseLLMProvider | None:
        all_providers = list(_PROVIDERS.keys())
        primary = settings.llm.provider
        fallbacks = [p for p in all_providers if p != primary]
        if fallbacks:
            return self._build_provider(fallbacks[0])
        return None

    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate a completion, falling back to the alternative provider on error.

        Args:
            prompt:        User message.
            temperature:   Override temperature (0.0–2.0).
            max_tokens:    Override max output tokens.
            system_prompt: System context injected before the user message.

        Returns:
            LLMResponse from the active (or fallback) provider.
        """
        try:
            response = await self._primary.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
            log.debug(
                f"LLM response: provider={response.provider} "
                f"tokens={response.input_tokens}+{response.output_tokens} "
                f"latency={response.latency_ms}ms"
            )
            return response
        except Exception as primary_exc:
            log.warning(
                f"Primary LLM ({self._primary.name}) failed: {primary_exc}. "
                f"Trying fallback..."
            )
            if self._fallback:
                return await self._fallback.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                )
            raise

    @property
    def provider_name(self) -> str:
        return self._primary.name

    @property
    def model_name(self) -> str:
        return self._primary.model
