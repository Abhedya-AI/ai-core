from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import get_logger
from app.modules.notifications.notification_channels import NotificationPayload, BaseNotificationChannel

log = get_logger("app.modules.notifications.escalation_matrix")

class EscalationTier(BaseModel):
    """Defines a single tier in an escalation policy."""
    model_config = ConfigDict(from_attributes=True)
    tier_level: int = Field(..., description="Level of the tier (1, 2, 3...)")
    timeout_minutes: int = Field(..., description="Minutes before escalating to next tier")
    channels: List[str] = Field(..., description="Channels to use for this tier")
    recipients: List[str] = Field(..., description="Recipients at this tier")

class EscalationPolicy(BaseModel):
    """Defines an entire multi-tier escalation policy."""
    model_config = ConfigDict(from_attributes=True)
    policy_id: str = Field(..., description="Unique ID for the policy")
    name: str = Field(..., description="Name of the escalation policy")
    tiers: List[EscalationTier] = Field(..., description="Ordered list of tiers")

class ActiveEscalation(BaseModel):
    """Represents an ongoing escalation incident."""
    model_config = ConfigDict(from_attributes=True)
    incident_id: str = Field(..., description="Unique ID for the incident")
    policy: EscalationPolicy = Field(..., description="The policy being applied")
    current_tier_index: int = Field(default=0, description="Current index in the policy tiers list")
    last_escalation_time: datetime = Field(default_factory=datetime.utcnow, description="Time of last escalation action")
    acknowledged: bool = Field(default=False, description="Whether the incident has been acknowledged")
    acknowledged_by: Optional[str] = Field(default=None, description="User who acknowledged the incident")

class EscalationMatrixManager:
    """Manages multi-tier escalation policies and active escalations."""
    
    def __init__(self, channel_registry: Dict[str, BaseNotificationChannel]):
        """Initialize the EscalationMatrixManager with available notification channels."""
        self.channel_registry = channel_registry
        self.active_escalations: Dict[str, ActiveEscalation] = {}
        self.policies: Dict[str, EscalationPolicy] = {}
    
    async def register_policy(self, policy: EscalationPolicy) -> None:
        """Register a new escalation policy."""
        self.policies[policy.policy_id] = policy
        log.info(f"Registered escalation policy {policy.policy_id}")

    async def trigger_escalation(self, incident_id: str, policy_id: str, title: str, message: str) -> bool:
        """Trigger an escalation process for an incident."""
        if policy_id not in self.policies:
            log.error(f"Policy {policy_id} not found.")
            return False
            
        policy = self.policies[policy_id]
        escalation = ActiveEscalation(
            incident_id=incident_id,
            policy=policy,
            current_tier_index=0
        )
        self.active_escalations[incident_id] = escalation
        
        await self._execute_tier(escalation, title, message)
        return True
        
    async def _execute_tier(self, escalation: ActiveEscalation, title: str, message: str) -> None:
        """Execute the notifications for the current tier."""
        tier = escalation.policy.tiers[escalation.current_tier_index]
        log.info(f"Executing tier {tier.tier_level} for incident {escalation.incident_id}")
        
        for recipient in tier.recipients:
            for channel_name in tier.channels:
                channel = self.channel_registry.get(channel_name)
                if channel:
                    payload = NotificationPayload(
                        title=f"[Tier {tier.tier_level}] {title}",
                        message=message,
                        recipient_id=recipient,
                        severity="CRITICAL"
                    )
                    await channel.send(payload)
                else:
                    log.warning(f"Channel {channel_name} not found in registry.")

    async def acknowledge_incident(self, incident_id: str, user_id: str) -> bool:
        """Acknowledge an incident, stopping further escalation."""
        if incident_id in self.active_escalations:
            escalation = self.active_escalations[incident_id]
            escalation.acknowledged = True
            escalation.acknowledged_by = user_id
            log.info(f"Incident {incident_id} acknowledged by {user_id}")
            return True
        return False

    async def evaluate_timeouts(self, title: str = "Escalation Update", message: str = "Timeout exceeded. Escalating.") -> None:
        """Check for active escalations that need to be bumped to the next tier."""
        now = datetime.utcnow()
        for incident_id, escalation in list(self.active_escalations.items()):
            if escalation.acknowledged:
                continue
                
            current_tier = escalation.policy.tiers[escalation.current_tier_index]
            timeout_delta = timedelta(minutes=current_tier.timeout_minutes)
            
            if now - escalation.last_escalation_time >= timeout_delta:
                if escalation.current_tier_index + 1 < len(escalation.policy.tiers):
                    escalation.current_tier_index += 1
                    escalation.last_escalation_time = now
                    log.info(f"Escalating incident {incident_id} to tier index {escalation.current_tier_index}")
                    await self._execute_tier(escalation, title, message)
                else:
                    log.warning(f"Incident {incident_id} exhausted all escalation tiers without acknowledgement.")
