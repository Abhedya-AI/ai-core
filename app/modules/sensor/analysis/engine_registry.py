import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.modules.sensor.domain.models import SensorReading, SensorAnomaly

log = get_logger("sensor.analysis.engine_registry")

class BaseAnomalyEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the engine."""
        pass

    @abstractmethod
    def analyze(self, reading: SensorReading, history: List[float]) -> List[SensorAnomaly]:
        """Analyze reading and history to detect anomalies."""
        pass

class AnomalyEngineRegistry:
    """Manages all anomaly detection engines."""
    
    def __init__(self):
        self._engines: Dict[str, BaseAnomalyEngine] = {}
        
        # Import engines internally to avoid circular dependencies
        from app.modules.sensor.analysis.engines.statistical_engine import StatisticalEngine
        from app.modules.sensor.analysis.engines.threshold_engine import ThresholdEngine
        from app.modules.sensor.analysis.engines.rate_of_change_engine import RateOfChangeEngine
        from app.modules.sensor.analysis.engines.pattern_engine import PatternEngine
        from app.modules.sensor.analysis.engines.correlation_engine import CorrelationEngine
        
        self.register(StatisticalEngine())
        self.register(ThresholdEngine())
        self.register(RateOfChangeEngine())
        self.register(PatternEngine())
        self.register(CorrelationEngine())

    def register(self, engine: BaseAnomalyEngine) -> None:
        """Register a new anomaly engine."""
        self._engines[engine.name] = engine
        log.info(f"Registered anomaly engine: {engine.name}")

    def analyze_reading(self, reading: SensorReading, history: List[float], sensor_config: Optional[Dict] = None) -> List[SensorAnomaly]:
        """Run all registered engines and merge deduplicated results."""
        all_anomalies = []
        for engine_name, engine in self._engines.items():
            try:
                # Merge sensor_config if provided
                if sensor_config:
                    if reading.metadata is None:
                        reading.metadata = {}
                    reading.metadata.update(sensor_config)
                
                anomalies = engine.analyze(reading, history)
                all_anomalies.extend(anomalies)
            except Exception as e:
                log.error(f"Error in {engine_name} while analyzing reading: {e}")
                
        # Merge and deduplicate based on anomaly_type and severity
        deduped = {}
        for anomaly in all_anomalies:
            key = f"{anomaly.anomaly_type.value}_{anomaly.severity.value}"
            if key not in deduped:
                deduped[key] = anomaly
            else:
                # Combine descriptions if needed, for simplicity we just keep the first one
                pass
        
        return list(deduped.values())

    def get_engine(self, name: str) -> Optional[BaseAnomalyEngine]:
        """Retrieve an engine by name."""
        return self._engines.get(name)

    def list_engines(self) -> List[str]:
        """List names of all registered engines."""
        return list(self._engines.keys())
