from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger
from ..domain.models import ModelVersion, ModelMetrics
from ..domain.enums import ModelStage, ModelStatus

log = get_logger(__name__)

class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelVersion] = {}
        # module -> champion model_id
        self._champion: dict[str, str] = {}

    async def register(self, name: str, description: str, version: str, module: str, model_family: str, feature_names: list[str], hyperparameters: dict[str, Any], tags: list[str], created_by: str, training_data_hash: str, deployment_config: dict[str, Any]) -> ModelVersion:
        start_t = time.perf_counter()
        
        model = ModelVersion(
            name=name,
            description=description,
            version=version,
            stage=ModelStage.DRAFT,
            status=ModelStatus.TRAINED,
            module=module,
            model_family=model_family,
            feature_names=feature_names,
            hyperparameters=hyperparameters,
            tags=tags,
            created_by=created_by,
            training_data_hash=training_data_hash,
            deployment_config=deployment_config,
            lineage_parent_ids=[]
        )
        
        self._models[model.model_id] = model
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Registered model {model.model_id} in {latency:.2f}ms")
        return model

    async def get(self, model_id: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        res = self._models.get(model_id)
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched model {model_id} in {latency:.2f}ms")
        return res

    async def list(self, module: str | None = None, stage: ModelStage | None = None, limit: int = 100, offset: int = 0) -> list[ModelVersion]:
        start_t = time.perf_counter()
        
        results = list(self._models.values())
        if module:
            results = [m for m in results if m.module == module]
        if stage:
            results = [m for m in results if m.stage == stage]
            
        results.sort(key=lambda x: x.created_at, reverse=True)
        results = results[offset:offset+limit]
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Listed {len(results)} models in {latency:.2f}ms")
        return results

    async def promote(self, model_id: str, to_stage: ModelStage, approved_by: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        
        model = self._models.get(model_id)
        if not model:
            return None
            
        if to_stage == ModelStage.PRODUCTION:
            current_champ_id = self._champion.get(model.module)
            if current_champ_id and current_champ_id in self._models:
                champ = self._models[current_champ_id]
                self._models[current_champ_id] = champ.model_copy(update={"stage": ModelStage.RETIRED})
                
            self._champion[model.module] = model_id
            
        updated = model.model_copy(update={"stage": to_stage, "approved_by": approved_by})
        self._models[model_id] = updated
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Promoted {model_id} to {to_stage} in {latency:.2f}ms")
        return updated

    async def rollback(self, module: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        
        # Find most recent RETIRED model for this module
        retired_models = [m for m in self._models.values() if m.module == module and m.stage == ModelStage.RETIRED]
        if not retired_models:
            log.warning(f"No retired models found for module {module} to rollback to.")
            return None
            
        retired_models.sort(key=lambda x: x.created_at, reverse=True)
        rollback_model = retired_models[0]
        
        # Retire current champion
        current_champ_id = self._champion.get(module)
        if current_champ_id and current_champ_id in self._models:
            champ = self._models[current_champ_id]
            self._models[current_champ_id] = champ.model_copy(update={"stage": ModelStage.RETIRED})
            
        # Promote rollback model to PRODUCTION
        promoted = rollback_model.model_copy(update={"stage": ModelStage.PRODUCTION})
        self._models[promoted.model_id] = promoted
        self._champion[module] = promoted.model_id
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Rolled back {module} to {promoted.model_id} in {latency:.2f}ms")
        return promoted

    async def retire(self, model_id: str, retired_by: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        
        model = self._models.get(model_id)
        if not model:
            return None
            
        updated = model.model_copy(update={"stage": ModelStage.RETIRED})
        self._models[model_id] = updated
        
        if self._champion.get(model.module) == model_id:
            del self._champion[model.module]
            
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Retired {model_id} in {latency:.2f}ms")
        return updated

    async def get_champion(self, module: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        champ_id = self._champion.get(module)
        res = self._models.get(champ_id) if champ_id else None
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched champion for {module} in {latency:.2f}ms")
        return res

    async def get_challenger(self, module: str) -> ModelVersion | None:
        start_t = time.perf_counter()
        staging_models = [m for m in self._models.values() if m.module == module and m.stage == ModelStage.STAGING]
        if not staging_models:
            return None
            
        staging_models.sort(key=lambda x: x.created_at, reverse=True)
        res = staging_models[0]
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Fetched challenger for {module} in {latency:.2f}ms")
        return res

    async def update_metrics(self, model_id: str, metrics: ModelMetrics) -> ModelVersion | None:
        start_t = time.perf_counter()
        
        model = self._models.get(model_id)
        if not model:
            return None
            
        updated = model.model_copy(update={"metrics": metrics})
        self._models[model_id] = updated
        
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Updated metrics for {model_id} in {latency:.2f}ms")
        return updated

    async def compare(self, model_id_a: str, model_id_b: str) -> dict[str, Any]:
        start_t = time.perf_counter()
        
        model_a = self._models.get(model_id_a)
        model_b = self._models.get(model_id_b)
        
        if not model_a or not model_b:
            return {"error": "One or both models not found"}
            
        metrics_a = model_a.metrics.model_dump() if model_a.metrics else {}
        metrics_b = model_b.metrics.model_dump() if model_b.metrics else {}
        
        comparison = {}
        all_keys = set(metrics_a.keys()).union(set(metrics_b.keys()))
        
        for k in all_keys:
            val_a = metrics_a.get(k)
            val_b = metrics_b.get(k)
            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                comparison[k] = {
                    "model_a": val_a,
                    "model_b": val_b,
                    "delta": float(val_b - val_a)
                }
                
        latency = (time.perf_counter() - start_t) * 1000
        log.info(f"Compared {model_id_a} and {model_id_b} in {latency:.2f}ms")
        return comparison

_service_instance = None

def get_model_registry() -> ModelRegistry:
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelRegistry()
    return _service_instance
