from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict
from app.core.logging import get_logger

log = get_logger(__name__)

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from app.modules.platform.domain.models import OrganizationProfile
except ImportError:
    class OrganizationProfile(BaseModel):
        model_config = ConfigDict(frozen=True)
        org_id: str
        tenant_id: str
        name: str
        description: str
        org_type: str
        parent_org_id: str | None
        plant_ids: list[str]
        member_ids: list[str]
        is_active: bool
        created_at: str
        updated_at: str

class OrganizationService:
    def __init__(self) -> None:
        self._orgs: dict[str, OrganizationProfile] = {}

    async def create(self, tenant_id: str, name: str, description: str, org_type: str, parent_org_id: str | None = None, plant_ids: list[str] = [], member_ids: list[str] = []) -> OrganizationProfile:
        start_time = time.perf_counter()
        try:
            org_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            org = OrganizationProfile(
                org_id=org_id,
                tenant_id=tenant_id,
                name=name,
                description=description,
                org_type=org_type,
                parent_org_id=parent_org_id,
                plant_ids=plant_ids,
                member_ids=member_ids,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            
            self._orgs[org_id] = org
            return org
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"Organization {name} created in {latency:.4f}s")

    async def get(self, org_id: str) -> OrganizationProfile | None:
        return self._orgs.get(org_id)

    async def list(self, tenant_id: str, org_type: str | None = None, parent_org_id: str | None = None, limit: int = 50, offset: int = 0) -> list[OrganizationProfile]:
        start_time = time.perf_counter()
        try:
            results = [o for o in self._orgs.values() if o.tenant_id == tenant_id]
            if org_type:
                results = [o for o in results if o.org_type == org_type]
            if parent_org_id is not None:
                results = [o for o in results if o.parent_org_id == parent_org_id]
            
            return results[offset:offset + limit]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"list organizations executed in {latency:.4f}s")

    async def update(self, org_id: str, updates: dict) -> OrganizationProfile:
        start_time = time.perf_counter()
        try:
            org = self._orgs.get(org_id)
            if not org:
                raise ValueError("Organization not found")
            
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated_org = org.model_copy(update=updates)
            self._orgs[org_id] = updated_org
            return updated_org
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"update organization executed in {latency:.4f}s")

    async def add_member(self, org_id: str, user_id: str) -> OrganizationProfile:
        org = await self.get(org_id)
        if not org:
            raise ValueError("Organization not found")
            
        if user_id not in org.member_ids:
            new_members = list(org.member_ids) + [user_id]
            return await self.update(org_id, {"member_ids": new_members})
        return org

    async def remove_member(self, org_id: str, user_id: str) -> OrganizationProfile:
        org = await self.get(org_id)
        if not org:
            raise ValueError("Organization not found")
            
        if user_id in org.member_ids:
            new_members = [m for m in org.member_ids if m != user_id]
            return await self.update(org_id, {"member_ids": new_members})
        return org

    async def add_plant(self, org_id: str, plant_id: str) -> OrganizationProfile:
        org = await self.get(org_id)
        if not org:
            raise ValueError("Organization not found")
            
        if plant_id not in org.plant_ids:
            new_plants = list(org.plant_ids) + [plant_id]
            return await self.update(org_id, {"plant_ids": new_plants})
        return org

    async def remove_plant(self, org_id: str, plant_id: str) -> OrganizationProfile:
        org = await self.get(org_id)
        if not org:
            raise ValueError("Organization not found")
            
        if plant_id in org.plant_ids:
            new_plants = [p for p in org.plant_ids if p != plant_id]
            return await self.update(org_id, {"plant_ids": new_plants})
        return org

    async def deactivate(self, org_id: str) -> OrganizationProfile:
        return await self.update(org_id, {"is_active": False})

    async def get_org_hierarchy(self, tenant_id: str) -> dict:
        start_time = time.perf_counter()
        try:
            orgs = [o for o in self._orgs.values() if o.tenant_id == tenant_id]
            
            if nx is None:
                log.warning("NetworkX not available, falling back to basic list structure.")
                return {
                    "root_orgs": [o.model_dump() for o in orgs if not o.parent_org_id],
                    "total_orgs": len(orgs),
                    "max_depth": 1
                }
                
            G = nx.DiGraph()
            for o in orgs:
                G.add_node(o.org_id, **o.model_dump())
                if o.parent_org_id:
                    G.add_edge(o.parent_org_id, o.org_id)

            roots = [n for n, d in G.in_degree() if d == 0]
            
            def build_tree(node_id: str) -> dict:
                node_data = G.nodes[node_id].copy()
                children = list(G.successors(node_id))
                node_data["children"] = [build_tree(child) for child in children]
                return node_data

            root_orgs = [build_tree(root) for root in roots]
            
            max_depth = 0
            if roots:
                try:
                    paths = dict(nx.all_pairs_shortest_path_length(G))
                    for root in roots:
                        if root in paths and paths[root]:
                            max_depth = max(max_depth, max(paths[root].values()))
                except Exception:
                    pass

            return {
                "root_orgs": root_orgs,
                "total_orgs": len(orgs),
                "max_depth": max_depth
            }
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_org_hierarchy executed in {latency:.4f}s")

    async def get_member_orgs(self, user_id: str, tenant_id: str) -> list[OrganizationProfile]:
        start_time = time.perf_counter()
        try:
            return [o for o in self._orgs.values() if o.tenant_id == tenant_id and user_id in o.member_ids]
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"get_member_orgs executed in {latency:.4f}s")

_service_instance = None
def get_service() -> OrganizationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = OrganizationService()
    return _service_instance
