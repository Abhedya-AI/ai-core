from __future__ import annotations
from typing import Protocol, runtime_checkable, Any, Type, Dict

from app.core.logging import get_logger
from app.modules.digital_twin.domain.enums import EntityType

log = get_logger(__name__)

@runtime_checkable
class AbstractTwinBuilder(Protocol):
    async def build(self, entity_id: str, context: dict[str, Any]) -> dict[str, Any]: ...
    async def update(self, current_state: dict[str, Any], new_data: dict[str, Any]) -> dict[str, Any]: ...
    def validate(self, state: dict[str, Any]) -> bool: ...


class TwinBuilderRegistry:
    _builders: Dict[EntityType, AbstractTwinBuilder] = {}

    @classmethod
    def register(cls, entity_type: EntityType, builder: AbstractTwinBuilder) -> None:
        cls._builders[entity_type] = builder
        log.info(f"Registered TwinBuilder for {entity_type}")

    @classmethod
    def get_builder(cls, entity_type: EntityType) -> AbstractTwinBuilder:
        if entity_type not in cls._builders:
            raise ValueError(f"No TwinBuilder registered for {entity_type}")
        return cls._builders[entity_type]
