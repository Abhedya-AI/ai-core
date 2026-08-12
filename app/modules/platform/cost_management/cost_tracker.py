from __future__ import annotations
import uuid
from datetime import datetime, timezone

from app.core.logging import get_logger
log = get_logger(__name__)

PRICING: dict[str, dict[str, float]] = {
    "COMMUNITY": {"api_call_usd": 0.0, "compute_unit_usd": 0.001, "storage_gb_usd": 0.0, "simulation_unit_usd": 0.01},
    "PROFESSIONAL": {"api_call_usd": 0.0001, "compute_unit_usd": 0.002, "storage_gb_usd": 0.05, "simulation_unit_usd": 0.02},
    "ENTERPRISE": {"api_call_usd": 0.00005, "compute_unit_usd": 0.0015, "storage_gb_usd": 0.03, "simulation_unit_usd": 0.015},
    "GOVERNMENT": {"api_call_usd": 0.00003, "compute_unit_usd": 0.001, "storage_gb_usd": 0.02, "simulation_unit_usd": 0.01},
}

class CostTracker:
    def __init__(self):
        self._usage: dict[str, dict] = {}
        self._records: dict[str, list[dict]] = {}

    def _ensure_tenant(self, tenant_id: str, tier: str) -> None:
        if tenant_id not in self._usage:
            self._usage[tenant_id] = {
                "api_calls": 0,
                "compute_units": 0.0,
                "storage_gb": 0.0,
                "simulation_units": 0,
                "tier": tier
            }
        else:
            self._usage[tenant_id]["tier"] = tier

    async def record_api_call(self, tenant_id: str, tier: str = "COMMUNITY", count: int = 1) -> None:
        self._ensure_tenant(tenant_id, tier)
        self._usage[tenant_id]["api_calls"] += count

    async def record_compute_usage(self, tenant_id: str, tier: str, units: float) -> None:
        self._ensure_tenant(tenant_id, tier)
        self._usage[tenant_id]["compute_units"] += units

    async def record_storage_usage(self, tenant_id: str, tier: str, gb: float) -> None:
        self._ensure_tenant(tenant_id, tier)
        self._usage[tenant_id]["storage_gb"] += gb

    async def record_simulation(self, tenant_id: str, tier: str, units: int = 1) -> None:
        self._ensure_tenant(tenant_id, tier)
        self._usage[tenant_id]["simulation_units"] += units

    async def compute_monthly_cost(self, tenant_id: str, period: str, tier: str = "COMMUNITY") -> dict:
        self._ensure_tenant(tenant_id, tier)
        usage = self._usage[tenant_id]
        tier_pricing = PRICING.get(tier, PRICING["COMMUNITY"])
        
        api_cost = usage["api_calls"] * tier_pricing["api_call_usd"]
        compute_cost = usage["compute_units"] * tier_pricing["compute_unit_usd"]
        storage_cost = usage["storage_gb"] * tier_pricing["storage_gb_usd"]
        simulation_cost = usage["simulation_units"] * tier_pricing["simulation_unit_usd"]
        
        total_cost = api_cost + compute_cost + storage_cost + simulation_cost
        
        record = {
            "record_id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "period": period,
            "api_cost_usd": api_cost,
            "compute_cost_usd": compute_cost,
            "storage_cost_usd": storage_cost,
            "simulation_cost_usd": simulation_cost,
            "total_cost_usd": total_cost,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if tenant_id not in self._records:
            self._records[tenant_id] = []
        self._records[tenant_id].append(record)
        return record

    async def get_current_usage(self, tenant_id: str) -> dict:
        usage = self._usage.get(tenant_id, {
            "api_calls": 0, "compute_units": 0.0, "storage_gb": 0.0, "simulation_units": 0, "tier": "COMMUNITY"
        })
        tier_pricing = PRICING.get(usage["tier"], PRICING["COMMUNITY"])
        
        estimated_cost = (
            usage["api_calls"] * tier_pricing["api_call_usd"] +
            usage["compute_units"] * tier_pricing["compute_unit_usd"] +
            usage["storage_gb"] * tier_pricing["storage_gb_usd"] +
            usage["simulation_units"] * tier_pricing["simulation_unit_usd"]
        )
        
        return {
            "api_calls": usage["api_calls"],
            "compute_units": usage["compute_units"],
            "storage_gb": usage["storage_gb"],
            "simulation_units": usage["simulation_units"],
            "estimated_cost_usd": estimated_cost
        }

    async def get_cost_history(self, tenant_id: str, limit: int = 12) -> list[dict]:
        records = self._records.get(tenant_id, [])
        return sorted(records, key=lambda x: x["period"], reverse=True)[:limit]

    async def get_fleet_costs(self, tenant_ids: list[str], period: str) -> dict:
        total = 0.0
        by_tenant = {}
        by_category = {"api": 0.0, "compute": 0.0, "storage": 0.0, "simulation": 0.0}
        
        for tid in tenant_ids:
            records = self._records.get(tid, [])
            record = next((r for r in records if r["period"] == period), None)
            if record:
                total += record["total_cost_usd"]
                by_tenant[tid] = record["total_cost_usd"]
                by_category["api"] += record["api_cost_usd"]
                by_category["compute"] += record["compute_cost_usd"]
                by_category["storage"] += record["storage_cost_usd"]
                by_category["simulation"] += record["simulation_cost_usd"]
                
        return {
            "total_cost_usd": total,
            "by_tenant": by_tenant,
            "by_category": by_category
        }

    async def reset_monthly_usage(self, tenant_id: str) -> None:
        if tenant_id in self._usage:
            tier = self._usage[tenant_id]["tier"]
            self._usage[tenant_id] = {
                "api_calls": 0,
                "compute_units": 0.0,
                "storage_gb": 0.0,
                "simulation_units": 0,
                "tier": tier
            }
