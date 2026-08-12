import uuid
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger

log = get_logger("app.modules.audit.audit_service")

class AuditRecord(BaseModel):
    """Immutable audit record representing significant system or user events."""
    model_config = ConfigDict(from_attributes=True)
    
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique audit record ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of the event")
    category: str = Field(..., description="Category: SENSOR, AGENT, WORKFLOW, USER, EMERGENCY")
    action: str = Field(..., description="Specific action performed")
    actor_id: str = Field(..., description="ID of the user, agent, or system component")
    target_id: Optional[str] = Field(default=None, description="ID of the entity acted upon")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured event details")
    hash_signature: str = Field(default="", description="Cryptographic signature for immutability validation")

class AuditService:
    """Service to generate, persist, and verify immutable audit records."""
    
    def __init__(self):
        """Initialize the AuditService. In production, this connects to an append-only store."""
        self._audit_log: List[AuditRecord] = []
        
    def _generate_signature(self, record: AuditRecord) -> str:
        """Generate a cryptographic hash signature for the record to ensure immutability."""
        record_dict = record.model_dump(exclude={"hash_signature"})
        # Simple JSON serialization for hashing; in production use robust canonical JSON
        content = json.dumps(record_dict, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    async def log_event(self, 
                        category: str, 
                        action: str, 
                        actor_id: str, 
                        target_id: Optional[str] = None, 
                        details: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """Create and securely log a generic audit event."""
        record = AuditRecord(
            category=category,
            action=action,
            actor_id=actor_id,
            target_id=target_id,
            details=details or {}
        )
        record.hash_signature = self._generate_signature(record)
        
        # Simulating persistence to immutable ledger
        self._audit_log.append(record)
        log.info(f"Audit record created: [{category}] {action} by {actor_id}")
        
        return record

    async def log_sensor_event(self, sensor_id: str, event_type: str, details: Dict[str, Any]) -> AuditRecord:
        """Helper to log sensor-related lifecycle and detection events."""
        return await self.log_event(
            category="SENSOR",
            action=event_type,
            actor_id="system",
            target_id=sensor_id,
            details=details
        )
        
    async def log_agent_decision(self, agent_name: str, decision_context: str, details: Dict[str, Any]) -> AuditRecord:
        """Helper to log AI agent decisions and reasoning context."""
        return await self.log_event(
            category="AGENT",
            action=decision_context,
            actor_id=agent_name,
            target_id=None,
            details=details
        )

    async def log_workflow_execution(self, workflow_id: str, status: str, details: Dict[str, Any]) -> AuditRecord:
        """Helper to log automated workflow execution results."""
        return await self.log_event(
            category="WORKFLOW",
            action=status,
            actor_id="workflow_engine",
            target_id=workflow_id,
            details=details
        )

    async def log_user_action(self, user_id: str, action: str, target_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """Helper to log explicit user actions within the system."""
        return await self.log_event(
            category="USER",
            action=action,
            actor_id=user_id,
            target_id=target_id,
            details=details
        )
        
    async def log_emergency_response(self, incident_id: str, action: str, actor_id: str, details: Dict[str, Any]) -> AuditRecord:
        """Helper to log critical emergency response actions."""
        return await self.log_event(
            category="EMERGENCY",
            action=action,
            actor_id=actor_id,
            target_id=incident_id,
            details=details
        )
        
    async def get_records(self, limit: int = 100, offset: int = 0) -> List[AuditRecord]:
        """Retrieve recent audit records (read-only query)."""
        return self._audit_log[offset:offset+limit]
        
    async def verify_chain(self) -> bool:
        """Verify the integrity of the in-memory audit log to detect tampering."""
        for record in self._audit_log:
            expected_hash = self._generate_signature(record)
            if record.hash_signature != expected_hash:
                log.error(f"Audit integrity failure detected for record {record.record_id}")
                return False
        return True
