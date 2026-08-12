import json
from typing import Any, Optional
from app.core.logging import get_logger
from app.modules.risk_prediction.domain.enums import EntityType
from app.modules.risk_prediction.domain.models import RiskAssessment, RiskForecast

log = get_logger(__name__)

try:
    from app.infrastructure.redis.client import get_client
except ImportError:
    def get_client(): return None

class RedisRiskCache:
    """Redis-backed cache for risk scores and feature vectors.
    TTLs: current risk score → 60s, forecast → 300s, features → 120s
    """
    
    def __init__(self):
        self.client = get_client()
        self._in_memory = {}
        
    def _key_assessment(self, entity_id: str, entity_type: EntityType) -> str:
        return f"risk:{entity_type.value}:{entity_id}:assessment"
        
    def _key_forecast(self, entity_id: str, entity_type: EntityType) -> str:
        return f"risk:{entity_type.value}:{entity_id}:forecast"
        
    def _key_features(self, entity_id: str) -> str:
        return f"risk:features:{entity_id}"
    
    async def cache_assessment(self, assessment: RiskAssessment, ttl: int = 60) -> None:
        key = self._key_assessment(assessment.entity_id, assessment.entity_type)
        data = assessment.model_dump_json()
        if self.client:
            await self.client.setex(key, ttl, data)
        else:
            self._in_memory[key] = data
            
    async def get_cached_assessment(
        self, entity_id: str, entity_type: EntityType
    ) -> Optional[RiskAssessment]:
        key = self._key_assessment(entity_id, entity_type)
        if self.client:
            data = await self.client.get(key)
        else:
            data = self._in_memory.get(key)
            
        if not data:
            return None
        return RiskAssessment.model_validate_json(data)
        
    async def cache_forecast(self, forecast: RiskForecast, ttl: int = 300) -> None:
        # Assuming forecast has entity_id and entity_type or we use generic
        # Wait, RiskForecast does not have entity_type in prompt but we can infer or pass
        entity_id = getattr(forecast, "entity_id", "unknown")
        entity_type = getattr(forecast, "entity_type", EntityType.EQUIPMENT)
        key = self._key_forecast(entity_id, entity_type)
        data = forecast.model_dump_json()
        if self.client:
            await self.client.setex(key, ttl, data)
        else:
            self._in_memory[key] = data
            
    async def get_cached_forecast(
        self, entity_id: str, entity_type: EntityType
    ) -> Optional[RiskForecast]:
        key = self._key_forecast(entity_id, entity_type)
        if self.client:
            data = await self.client.get(key)
        else:
            data = self._in_memory.get(key)
            
        if not data:
            return None
        return RiskForecast.model_validate_json(data)
        
    async def cache_features(
        self, entity_id: str, features: dict, ttl: int = 120
    ) -> None:
        key = self._key_features(entity_id)
        data = json.dumps(features)
        if self.client:
            await self.client.setex(key, ttl, data)
        else:
            self._in_memory[key] = data
            
    async def get_cached_features(
        self, entity_id: str
    ) -> Optional[dict]:
        key = self._key_features(entity_id)
        if self.client:
            data = await self.client.get(key)
        else:
            data = self._in_memory.get(key)
            
        if not data:
            return None
        return json.loads(data)
        
    async def invalidate(self, entity_id: str, entity_type: EntityType) -> None:
        keys = [
            self._key_assessment(entity_id, entity_type),
            self._key_forecast(entity_id, entity_type),
            self._key_features(entity_id)
        ]
        if self.client:
            await self.client.delete(*keys)
        else:
            for k in keys:
                self._in_memory.pop(k, None)
                
    async def get_all_current_risks(self) -> list[dict]:
        """Scan Redis for all cached risk scores (for dashboard)."""
        if self.client:
            keys = await self.client.keys("risk:*:*:assessment")
            if not keys:
                return []
            vals = await self.client.mget(keys)
            return [json.loads(v) for v in vals if v]
        else:
            return [json.loads(v) for k, v in self._in_memory.items() if ":assessment" in k]
