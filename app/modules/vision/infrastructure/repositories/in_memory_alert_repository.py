"""
vision/infrastructure/repositories/in_memory_alert_repository.py

In-memory implementation of AlertRepository for testing and development.
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Any

from app.core.logging import get_logger
from app.modules.vision.domain.repositories.alert_repository import AlertRepository
from app.modules.vision.domain.entities.vision_alert import VisionAlert

log = get_logger("vision.infrastructure.repos.alert")

class InMemoryAlertRepository(AlertRepository):
    def __init__(self):
        self._alerts: dict[str, VisionAlert] = {}
        self._lock = asyncio.Lock()

    async def save_alert(self, alert: VisionAlert) -> VisionAlert:
        async with self._lock:
            self._alerts[alert.alert_id] = alert
        return alert

    async def get_alert(self, alert_id: str) -> VisionAlert | None:
        async with self._lock:
            return self._alerts.get(alert_id)

    async def update_alert(self, alert: VisionAlert) -> VisionAlert:
        async with self._lock:
            self._alerts[alert.alert_id] = alert
        return alert

    async def list_alerts(
        self,
        zone_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        camera_id: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[VisionAlert]:
        async with self._lock:
            alerts = list(self._alerts.values())
            if zone_id:
                alerts = [a for a in alerts if a.zone_id == zone_id]
            if severity:
                alerts = [a for a in alerts if (getattr(a.severity, "value", a.severity) == severity)]
            if status:
                alerts = [a for a in alerts if (getattr(a.status, "value", a.status) == status)]
            if camera_id:
                alerts = [a for a in alerts if a.camera_id == camera_id]
            
            alerts.sort(key=lambda a: a.created_at, reverse=True)
            return alerts[offset:offset+limit]

    async def count_active_alerts(self, zone_id: str | None = None) -> int:
        async with self._lock:
            alerts = [a for a in self._alerts.values() if a.is_active]
            if zone_id:
                alerts = [a for a in alerts if a.zone_id == zone_id]
            return len(alerts)
