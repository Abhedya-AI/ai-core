"""
llm/providers/base.py — Abstract LLM provider interface.

Every provider (Gemini, Groq, OpenAI) implements this interface.
The LLMGateway routes calls to the active provider.

Never call providers directly from outside the llm/ module.
Always use: from app.infrastructure.llm.gateway import LLMGateway
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standard response from any LLM provider."""
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class BaseLLMProvider(ABC):
    """Abstract interface that all LLM providers must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'gemini', 'groq')."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Active model name (e.g. 'gemini-2.5-flash')."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate a completion from the provider.

        Args:
            prompt:         User prompt text.
            temperature:    Override the default temperature (0.0–2.0).
            max_tokens:     Override the default max output tokens.
            system_prompt:  Optional system/context prompt.

        Returns:
            LLMResponse with text, token counts, and latency.
        """

    @abstractmethod
    async def is_available(self) -> bool:
        """Return True if the provider can accept requests right now."""
