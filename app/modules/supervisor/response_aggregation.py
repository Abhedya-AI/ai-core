from typing import Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.modules.agents.core.agent_result import AgentResult
from app.core.logging import get_logger

log = get_logger(__name__)

class AggregatedAssessment(BaseModel):
    """Unified safety assessment from multiple agent findings."""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(description="Overall status of the assessment")
    critical_findings: List[str] = Field(default_factory=list, description="Critical issues detected")
    recommendations: List[str] = Field(default_factory=list, description="Suggested actions")
    agent_data: Dict[str, Any] = Field(default_factory=dict, description="Raw data from individual agents")

class ResponseAggregator:
    """Synthesizes findings into unified safety assessment."""
    
    def aggregate(self, agent_results: Dict[str, AgentResult]) -> AggregatedAssessment:
        """
        Aggregate results from multiple agents into a single assessment.
        
        Args:
            agent_results: A mapping of agent IDs to their execution results.
            
        Returns:
            An aggregated assessment.
        """
        assessment = AggregatedAssessment(status="healthy")
        
        has_error = False
        has_warning = False
        
        for agent_id, result in agent_results.items():
            if result.status == "error":
                has_error = True
                assessment.critical_findings.append(f"[{agent_id}] Error: {result.error}")
            elif result.status == "warning":
                has_warning = True
                
            assessment.agent_data[agent_id] = result.data
            
            if isinstance(result.data, dict):
                findings = result.data.get("findings", [])
                if findings:
                    assessment.critical_findings.extend(f"[{agent_id}] {f}" for f in findings)
                    
                recs = result.data.get("recommendations", [])
                if recs:
                    assessment.recommendations.extend(f"[{agent_id}] {r}" for r in recs)
                    
        if has_error:
            assessment.status = "critical"
        elif has_warning or assessment.critical_findings:
            assessment.status = "warning"
            
        log.info(f"Aggregated response created with status: {assessment.status}")
        return assessment
