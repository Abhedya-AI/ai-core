"""grounded_generation.py — Grounded Answer Generator using LLMGateway."""

from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.infrastructure.llm.gateway import LLMGateway
from app.modules.graphrag.generation.citations import Citation, assemble_citations
from app.modules.graphrag.generation.prompts import GRAPHRAG_SYSTEM_PROMPT, GRAPHRAG_USER_TEMPLATE
from app.modules.graphrag.ranking.fusion import FusedEvidence

log = get_logger("graphrag.generation.grounded")


class GroundedAnswer(BaseModel):
    """Complete grounded answer DTO returned by GraphRAG."""

    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[FusedEvidence] = Field(default_factory=list)
    provider_used: str = "LLMGateway"
    latency_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GroundedAnswerGenerator:
    """Generates grounded answers by prompting LLMGateway with structured evidence context."""

    def __init__(self, llm_gateway: LLMGateway | None = None) -> None:
        self._llm = llm_gateway or LLMGateway.get()

    async def generate_grounded_answer(
        self,
        question: str,
        context_block: str,
        evidence_items: list[FusedEvidence],
    ) -> GroundedAnswer:
        """
        Prompt LLMGateway and assemble grounded response with citations.

        Returns:
            GroundedAnswer DTO.
        """
        user_prompt = GRAPHRAG_USER_TEMPLATE.format(question=question, context_block=context_block)
        log.info(f"Generating grounded answer for: '{question[:60]}...'")

        # Call LLM Gateway
        response = await self._llm.generate(
            prompt=user_prompt,
            system_instruction=GRAPHRAG_SYSTEM_PROMPT,
            temperature=0.2,   # Low temperature for strict factual grounding
        )

        citations = assemble_citations(evidence_items)

        return GroundedAnswer(
            question=question,
            answer=response.text,
            citations=citations,
            evidence=evidence_items,
            provider_used=response.provider,
            latency_ms=response.latency_ms,
            metadata={
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
