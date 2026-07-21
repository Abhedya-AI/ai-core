"""execution_plan.py — Multi-agent ExecutionPlan & ExecutionStage models."""

from pydantic import BaseModel, Field

from app.modules.agents.core.types import Capability


class ExecutionStage(BaseModel):
    """
    Stage representing parallel or sequential execution of agents.
    """

    stage_name: str
    required_capabilities: list[Capability] = Field(default_factory=list)
    agent_names: list[str] = Field(default_factory=list)
    depends_on_stages: list[str] = Field(default_factory=list)
    allow_parallel: bool = True
    max_retries: int = 2


class ExecutionPlan(BaseModel):
    """
    Plan constructed by Supervisor specifying multi-agent stages and dependencies.
    """

    task_id: str
    task_statement: str
    stages: list[ExecutionStage] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
