"""memory.py — Execution memory store for intermediate agent reasoning."""

from typing import Any

from pydantic import BaseModel, Field


class AgentExecutionMemory(BaseModel):
    """
    Execution memory for sharing intermediate facts, graph context, and LLM outputs across agents.
    """

    task_id: str
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    retrieved_graph: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: list[dict[str, Any]] = Field(default_factory=list)
    llm_outputs: list[str] = Field(default_factory=list)
    cached_embeddings: dict[str, list[float]] = Field(default_factory=dict)
    previous_decisions: list[dict[str, Any]] = Field(default_factory=list)
