from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger
from ..domain.models import ModelVersion
from .registry import ModelRegistry

log = get_logger(__name__)

class ModelVersionManager:
    async def next_version(self, current_version: str, bump: str) -> str:
        start_t = time.perf_counter()
        
        try:
            parts = [int(p) for p in current_version.split(".")]
            if len(parts) != 3:
                parts = [0, 1, 0] # fallback
        except ValueError:
            parts = [0, 1, 0]
            
        if bump == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif bump == "minor":
            parts[1] += 1
            parts[2] = 0
        elif bump == "patch":
            parts[2] += 1
            
        new_v = f"{parts[0]}.{parts[1]}.{parts[2]}"
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Bumped version from {current_version} to {new_v} in {latency:.2f}ms")
        return new_v

    async def diff(self, version_a: ModelVersion, version_b: ModelVersion) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        changed_fields = []
        if version_a.hyperparameters != version_b.hyperparameters:
            changed_fields.append("hyperparameters")
        if version_a.feature_names != version_b.feature_names:
            changed_fields.append("feature_names")
        if version_a.training_data_hash != version_b.training_data_hash:
            changed_fields.append("training_data_hash")
            
        metric_deltas = {}
        if version_a.metrics and version_b.metrics:
            ma = version_a.metrics.model_dump()
            mb = version_b.metrics.model_dump()
            for k in ma:
                if isinstance(ma[k], (int, float)) and isinstance(mb.get(k), (int, float)):
                    metric_deltas[k] = float(mb[k] - ma[k])
                    
        hp_changes = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        for k, v in version_b.hyperparameters.items():
            if k not in version_a.hyperparameters:
                hp_changes["added"][k] = v
            elif version_a.hyperparameters[k] != v:
                hp_changes["modified"][k] = {"from": version_a.hyperparameters[k], "to": v}
                
        for k, v in version_a.hyperparameters.items():
            if k not in version_b.hyperparameters:
                hp_changes["removed"][k] = v

        diff_res = {
            "changed_fields": changed_fields,
            "metric_deltas": metric_deltas,
            "hyperparameter_changes": hp_changes
        }
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Diffed {version_a.model_id} and {version_b.model_id} in {latency:.2f}ms")
        return diff_res

    async def changelog(self, model_id: str, registry: ModelRegistry) -> list[dict[str, Any]]:
        start_t = time.perf_counter()
        
        target_model = await registry.get(model_id)
        if not target_model:
            return []
            
        all_models = await registry.list(module=target_model.module, limit=1000)
        # Filter same name
        family_models = [m for m in all_models if m.name == target_model.name]
        family_models.sort(key=lambda x: x.created_at)
        
        cl = []
        for m in family_models:
            cl.append({
                "version": m.version,
                "stage": m.stage,
                "created_at": m.created_at,
                "created_by": m.created_by,
                "metrics_summary": m.metrics.model_dump() if m.metrics else None
            })
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Generated changelog for {model_id} in {latency:.2f}ms")
        return cl

    async def is_valid_semver(self, version: str) -> bool:
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(p.isdigit() for p in parts)

    async def suggest_version(self, current: str, metric_delta: float) -> str:
        start_t = time.perf_counter()
        
        if metric_delta > 0.1:
            bump = "major"
        elif metric_delta > 0.02:
            bump = "minor"
        else:
            bump = "patch"
            
        new_v = await self.next_version(current, bump)
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Suggested version {new_v} based on delta {metric_delta} in {latency:.2f}ms")
        return new_v

_service_instance = None

def get_version_manager() -> ModelVersionManager:
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelVersionManager()
    return _service_instance
