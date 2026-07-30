"""
app/services/incident_service.py — Incident Lifecycle Service.

An "Incident" in ABHEDYA is any detected safety event requiring investigation.

Lifecycle:
  OPEN → INVESTIGATING → RESPONDED → CLOSED

This service:
  1. Creates incident records
  2. Triggers full Supervisor multi-agent investigation
  3. Persists investigation results
  4. Manages incident status transitions
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents import AgentRegistry, SupervisorAgent
from app.modules.agents.core.orchestrator import AgentOrchestrator
from app.modules.auth.models import Principal
from app.services.base import BaseService

log = get_logger("services.incident")


# ── Incident Model (in-memory, production: PostgreSQL) ─────────────────────────

class Incident:
    """Lightweight in-memory incident record."""

    def __init__(
        self,
        incident_id: str,
        title: str,
        description: str,
        zone_id: str | None,
        target_entity_id: str | None,
        severity: str,
        created_by: str,
    ) -> None:
        self.incident_id = incident_id
        self.title = title
        self.description = description
        self.zone_id = zone_id
        self.target_entity_id = target_entity_id
        self.severity = severity
        self.status = "OPEN"
        self.created_by = created_by
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.investigation_results: list[dict[str, Any]] = []
        self.closed_at: datetime | None = None
        self.resolution_notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "zone_id": self.zone_id,
            "target_entity_id": self.target_entity_id,
            "severity": self.severity,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "investigation_results": self.investigation_results,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "resolution_notes": self.resolution_notes,
        }


class IncidentStore:
    """In-memory incident store (replace with async DB repository in production)."""

    _instance: "IncidentStore | None" = None

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}

    @classmethod
    def get_instance(cls) -> "IncidentStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def save(self, incident: Incident) -> None:
        self._incidents[incident.incident_id] = incident

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def list_all(self, limit: int = 50) -> list[Incident]:
        return list(reversed(list(self._incidents.values())))[:limit]


# ── Service ────────────────────────────────────────────────────────────────────

class IncidentService(BaseService):
    """
    Manages incident lifecycle — from creation through investigation and closure.
    """

    def __init__(
        self,
        store: IncidentStore | None = None,
        registry: AgentRegistry | None = None,
    ) -> None:
        self._store = store or IncidentStore.get_instance()
        self._registry = registry or AgentRegistry.get_instance()

    async def create_incident(
        self,
        title: str,
        description: str,
        *,
        zone_id: str | None = None,
        target_entity_id: str | None = None,
        severity: str = "MEDIUM",
        principal: Principal | None = None,
        auto_investigate: bool = True,
    ) -> dict[str, Any]:
        """
        Create an incident and optionally trigger automatic investigation.

        Args:
            title: Short incident title.
            description: Detailed description / query for the AI.
            zone_id: Affected zone.
            target_entity_id: Primary asset/entity ID.
            severity: LOW | MEDIUM | HIGH | CRITICAL.
            principal: Authenticated caller.
            auto_investigate: If True, immediately run Supervisor investigation.

        Returns:
            Incident dict with investigation_results populated if auto_investigate=True.
        """
        incident_id = str(uuid.uuid4())
        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            zone_id=zone_id,
            target_entity_id=target_entity_id,
            severity=severity,
            created_by=principal.user_id if principal else "system",
        )
        incident.status = "OPEN"
        self._store.save(incident)
        log.info(f"Incident created: {incident_id} — '{title}' (severity={severity})")

        if auto_investigate:
            incident.status = "INVESTIGATING"
            self._store.save(incident)
            try:
                results = await self._run_investigation(incident, principal)
                incident.investigation_results = results
                incident.status = "INVESTIGATED"
            except Exception as exc:
                log.error(f"Investigation failed for incident {incident_id}: {exc}")
                incident.status = "OPEN"
            incident.updated_at = datetime.now(timezone.utc)
            self._store.save(incident)

        return incident.to_dict()

    async def get_incident(self, incident_id: str) -> dict[str, Any]:
        """Retrieve an incident by ID."""
        from app.api.exceptions import NotFoundError
        incident = self._store.get(incident_id)
        if not incident:
            raise NotFoundError(message=f"Incident '{incident_id}' not found.")
        return incident.to_dict()

    async def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent incidents."""
        return [i.to_dict() for i in self._store.list_all(limit)]

    async def investigate(
        self,
        incident_id: str,
        principal: Principal | None = None,
    ) -> dict[str, Any]:
        """Manually trigger investigation on an existing incident."""
        from app.api.exceptions import NotFoundError
        incident = self._store.get(incident_id)
        if not incident:
            raise NotFoundError(message=f"Incident '{incident_id}' not found.")

        incident.status = "INVESTIGATING"
        self._store.save(incident)
        results = await self._run_investigation(incident, principal)
        incident.investigation_results = results
        incident.status = "INVESTIGATED"
        incident.updated_at = datetime.now(timezone.utc)
        self._store.save(incident)
        return incident.to_dict()

    async def close_incident(
        self,
        incident_id: str,
        resolution_notes: str,
        principal: Principal | None = None,
    ) -> dict[str, Any]:
        """Close an incident with resolution notes."""
        from app.api.exceptions import NotFoundError
        incident = self._store.get(incident_id)
        if not incident:
            raise NotFoundError(message=f"Incident '{incident_id}' not found.")

        incident.status = "CLOSED"
        incident.resolution_notes = resolution_notes
        incident.closed_at = datetime.now(timezone.utc)
        incident.updated_at = datetime.now(timezone.utc)
        self._store.save(incident)
        log.info(f"Incident {incident_id} closed by {principal.user_id if principal else 'system'}")
        return incident.to_dict()

    # ── Private ────────────────────────────────────────────────────────────────

    async def _run_investigation(
        self, incident: Incident, principal: Principal | None
    ) -> list[dict[str, Any]]:
        """Run the Supervisor orchestration for this incident."""
        ctx = self._build_context(
            query=incident.description,
            intent="GENERAL_SAFETY",
            principal=principal,
            target_entity_id=incident.target_entity_id,
            zone_id=incident.zone_id,
        )
        supervisor = SupervisorAgent(registry=self._registry)
        plan = await supervisor.create_plan(ctx)
        orchestrator = AgentOrchestrator(registry=self._registry)
        results, _ = await orchestrator.execute_plan(plan, ctx)

        return [
            {
                "agent": r.agent_name,
                "success": r.success,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "recommendations": r.recommendations,
                "explanation": r.explanation,
            }
            for r in results
        ]


# ── Singleton ──────────────────────────────────────────────────────────────────

_incident_svc: IncidentService | None = None


def get_incident_service() -> IncidentService:
    global _incident_svc
    if _incident_svc is None:
        _incident_svc = IncidentService()
    return _incident_svc
