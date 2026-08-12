from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from app.modules.platform.domain.models import PlantProfile
    from app.modules.platform.domain.enums import PlantStatus
except ImportError:
    PlantStatus = str
    class PlantProfile(BaseModel):
        model_config = ConfigDict(frozen=True)
        plant_id: str
        tenant_id: str
        name: str
        location: str
        description: str
        plant_type: str
        timezone: str
        status: PlantStatus
        oee_score: float
        safety_index: float
        equipment_count: int
        worker_count: int
        metadata: dict
        created_at: str
        updated_at: str

class PlantRegistry:
    def __init__(self) -> None:
        self._plants: dict[str, PlantProfile] = {}
        self._tenant_plants: dict[str, list[str]] = {}

    async def register(self, tenant_id: str, name: str, location: str, description: str, plant_type: str, timezone_str: str = "UTC", metadata: dict = {}) -> PlantProfile:
        start_time = time.perf_counter()
        try:
            plant_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            plant = PlantProfile(
                plant_id=plant_id,
                tenant_id=tenant_id,
                name=name,
                location=location,
                description=description,
                plant_type=plant_type,
                timezone=timezone_str,
                status="ACTIVE",
                oee_score=0.0,
                safety_index=1.0,
                equipment_count=0,
                worker_count=0,
                metadata=metadata,
                created_at=now,
                updated_at=now
            )
            
            self._plants[plant_id] = plant
            if tenant_id not in self._tenant_plants:
                self._tenant_plants[tenant_id] = []
            self._tenant_plants[tenant_id].append(plant_id)
            
            return plant
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"register plant executed in {latency:.4f}s")

    async def get(self, plant_id: str) -> PlantProfile | None:
        return self._plants.get(plant_id)

    async def list(self, tenant_id: str, status: PlantStatus | None = None, limit: int = 50, offset: int = 0) -> list[PlantProfile]:
        start_time = time.perf_counter()
        try:
            plant_ids = self._tenant_plants.get(tenant_id, [])
            results = [self._plants[pid] for pid in plant_ids if pid in self._plants]
            
            if status:
                results = [p for p in results if p.status == status]
                
            return results[offset:offset + limit]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list plants executed in {latency:.4f}s")

    async def update(self, plant_id: str, updates: dict) -> PlantProfile:
        start_time = time.perf_counter()
        try:
            plant = self._plants.get(plant_id)
            if not plant:
                raise ValueError("Plant not found")
                
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated_plant = plant.model_copy(update=updates)
            self._plants[plant_id] = updated_plant
            return updated_plant
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"update plant executed in {latency:.4f}s")

    async def update_status(self, plant_id: str, status: PlantStatus) -> PlantProfile:
        return await self.update(plant_id, {"status": status})

    async def update_metrics(self, plant_id: str, oee_score: float | None = None, safety_index: float | None = None, equipment_count: int | None = None, worker_count: int | None = None) -> PlantProfile:
        updates = {}
        if oee_score is not None:
            updates["oee_score"] = oee_score
        if safety_index is not None:
            updates["safety_index"] = safety_index
        if equipment_count is not None:
            updates["equipment_count"] = equipment_count
        if worker_count is not None:
            updates["worker_count"] = worker_count
            
        return await self.update(plant_id, updates)

    async def deregister(self, plant_id: str) -> bool:
        start_time = time.perf_counter()
        try:
            if plant_id in self._plants:
                plant = self._plants[plant_id]
                tenant_id = plant.tenant_id
                
                del self._plants[plant_id]
                if tenant_id in self._tenant_plants and plant_id in self._tenant_plants[tenant_id]:
                    self._tenant_plants[tenant_id].remove(plant_id)
                return True
            return False
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"deregister plant executed in {latency:.4f}s")

    async def count_by_tenant(self, tenant_id: str) -> int:
        return len(self._tenant_plants.get(tenant_id, []))

    async def get_all_active(self) -> list[PlantProfile]:
        return [p for p in self._plants.values() if p.status == "ACTIVE"]

_service_instance = None
def get_service() -> PlantRegistry:
    global _service_instance
    if _service_instance is None:
        _service_instance = PlantRegistry()
    return _service_instance
