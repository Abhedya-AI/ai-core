from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.modules.digital_twin.domain.models import ResourceTwin, _now_iso

log = get_logger(__name__)

class ResourceTwinBuilder:
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]:
        resource_data = context.get("resource_data", {})
        
        qty_available = resource_data.get("quantity_available", 0.0)
        consumption_rate = resource_data.get("consumption_rate", 0.0)
        
        depletion = None
        if consumption_rate > 0:
            depletion = qty_available / consumption_rate
            
        twin = ResourceTwin(
            resource_id=entity_id,
            resource_name=resource_data.get("resource_name", f"Resource-{entity_id}"),
            resource_type=resource_data.get("resource_type", "MATERIAL"),
            zone_id=resource_data.get("zone_id"),
            quantity_available=qty_available,
            quantity_total=resource_data.get("quantity_total", qty_available),
            unit=resource_data.get("unit", "units"),
            is_critical=resource_data.get("is_critical", False),
            last_replenished_at=resource_data.get("last_replenished_at"),
            consumption_rate=consumption_rate,
            estimated_depletion_hours=depletion
        )
        return twin.model_dump()

    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]:
        updated = dict(current_state)
        rd = new_data.get("resource_data", {})
        
        if "quantity_available" in rd: updated["quantity_available"] = rd["quantity_available"]
        if "consumption_rate" in rd: updated["consumption_rate"] = rd["consumption_rate"]
        
        qty = updated.get("quantity_available", 0.0)
        rate = updated.get("consumption_rate", 0.0)
        updated["estimated_depletion_hours"] = (qty / rate) if rate > 0 else None
            
        updated["updated_at"] = _now_iso()
        return updated

    def validate(self, state: dict[str, Any]) -> bool:
        required = ["resource_id", "resource_name", "quantity_available", "quantity_total"]
        return all(k in state for k in required)
