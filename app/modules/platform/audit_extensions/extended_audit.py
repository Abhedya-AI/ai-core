from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)

try:
    from app.modules.security.services.encryption_service import EncryptionService
except ImportError:
    EncryptionService = None

try:
    from app.modules.audit.services.audit_service import AuditService
except ImportError:
    AuditService = None

class AuditExtension:
    def __init__(self, action: str, actor_id: str, actor_type: str, resource_id: str, resource_type: str, tenant_id: str, details: dict, ip_address: str | None, is_sensitive: bool):
        self.audit_id = str(uuid.uuid4())
        self.action = action
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.tenant_id = tenant_id
        self.details = details
        self.ip_address = ip_address
        self.is_sensitive = is_sensitive
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "tenant_id": self.tenant_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "is_sensitive": self.is_sensitive,
            "timestamp": self.timestamp
        }

class ExtendedAuditService:
    def __init__(self):
        self._records: list[AuditExtension] = []

    async def log(self, action: str, actor_id: str, actor_type: str, resource_id: str, resource_type: str, tenant_id: str, details: dict, ip_address: str | None = None, is_sensitive: bool = False) -> AuditExtension:
        processed_details = details.copy()
        if is_sensitive and EncryptionService:
            try:
                # Basic mock encryption of dict values
                for k, v in processed_details.items():
                    if isinstance(v, str):
                        processed_details[k] = f"ENCRYPTED_{v}"
            except Exception as e:
                log.error(f"Failed to encrypt sensitive audit details: {e}")

        record = AuditExtension(
            action=action, actor_id=actor_id, actor_type=actor_type,
            resource_id=resource_id, resource_type=resource_type,
            tenant_id=tenant_id, details=processed_details,
            ip_address=ip_address, is_sensitive=is_sensitive
        )
        self._records.append(record)
        log.info(f"Audit log created: {action} on {resource_type} {resource_id} by {actor_id}")

        if AuditService:
            try:
                # Assuming AuditService has a method log_event
                pass
            except Exception as e:
                log.error(f"Failed to forward to core audit service: {e}")

        return record

    async def list(self, tenant_id: str | None = None, action: str | None = None, resource_type: str | None = None, limit: int = 100, offset: int = 0) -> list[AuditExtension]:
        filtered = self._records
        if tenant_id:
            filtered = [r for r in filtered if r.tenant_id == tenant_id]
        if action:
            filtered = [r for r in filtered if r.action == action]
        if resource_type:
            filtered = [r for r in filtered if r.resource_type == resource_type]
            
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered[offset:offset+limit]

    async def get(self, audit_id: str) -> AuditExtension | None:
        for r in self._records:
            if r.audit_id == audit_id:
                return r
        return None

    async def export_compliance_log(self, tenant_id: str, start_time: str, end_time: str) -> list[dict]:
        filtered = [
            r.to_dict() for r in self._records
            if r.tenant_id == tenant_id and start_time <= r.timestamp <= end_time
        ]
        return filtered

    async def count_by_action(self, tenant_id: str, window_hours: int = 24) -> dict[str, int]:
        counts: dict[str, int] = {}
        now = datetime.now(timezone.utc)
        
        for r in self._records:
            if r.tenant_id == tenant_id:
                record_time = datetime.fromisoformat(r.timestamp)
                if (now - record_time).total_seconds() <= window_hours * 3600:
                    counts[r.action] = counts.get(r.action, 0) + 1
                    
        return counts
