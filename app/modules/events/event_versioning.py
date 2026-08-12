"""
Event version manager handling schema versioning and backward compatibility.
"""
from typing import Dict, Any, Callable
from app.core.logging import get_logger

log = get_logger("app.modules.events.event_versioning")

class EventVersionManager:
    """Manages event schema versions and migrations."""

    def __init__(self) -> None:
        """Initialize the event version manager."""
        self._upcasters: Dict[str, Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = {}

    def register_upcaster(
        self, 
        event_type: str, 
        from_version: str, 
        upcaster_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Register a function to upgrade an event payload from an older version.
        
        Args:
            event_type: The type of the event.
            from_version: The version to migrate from (e.g., 'v1').
            upcaster_func: Function that takes the old payload and returns the new one.
        """
        if event_type not in self._upcasters:
            self._upcasters[event_type] = {}
        
        self._upcasters[event_type][from_version] = upcaster_func
        log.info(f"Registered upcaster for {event_type} from {from_version}")

    def upcast_event(
        self, 
        event_type: str, 
        payload: Dict[str, Any], 
        current_version: str
    ) -> Dict[str, Any]:
        """
        Upcast an event payload to the latest version.
        
        Args:
            event_type: The type of the event.
            payload: The event payload to upcast.
            current_version: The current version of the payload.
            
        Returns:
            The upcasted payload.
        """
        if event_type not in self._upcasters:
            return payload
            
        upcasters_for_type = self._upcasters[event_type]
        upcasted_payload = payload
        version = current_version
        
        while version in upcasters_for_type:
            try:
                upcast_func = upcasters_for_type[version]
                upcasted_payload = upcast_func(upcasted_payload)
                # Convention: the upcaster should update a 'version' field or we track it externally
                version = upcasted_payload.get("version", "unknown")
            except Exception as e:
                log.error(f"Failed to upcast event {event_type} from version {version}: {str(e)}")
                raise ValueError(f"Upcast failed for {event_type} at version {version}") from e
                
        return upcasted_payload
