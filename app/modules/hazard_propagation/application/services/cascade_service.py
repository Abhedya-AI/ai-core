from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger

log = get_logger(__name__)

class CascadeService:
    def __init__(self) -> None:
        self._detector = None
        self._builder = None
        self._calculator = None
        self._init_engines()

    def _init_engines(self) -> None:
        try:
            from app.modules.hazard_propagation.application.cascade_engine.detector import CascadeDetector
            from app.modules.hazard_propagation.application.cascade_engine.chain_builder import FailureChainBuilder
            from app.modules.hazard_propagation.application.cascade_engine.probability_calc import CascadeProbabilityCalculator
            self._detector = CascadeDetector()
            self._builder = FailureChainBuilder()
            self._calculator = CascadeProbabilityCalculator()
        except ImportError as e:
            log.warning(f"Cascade engines not available: {e}")

    async def detect(self, propagation_id: str, hazard_type: str, intensity: float, zone_conditions: dict[str, Any], source_node_id: str) -> dict[str, Any]:
        t0 = time.perf_counter()
        
        cascades = []
        if self._detector:
            try:
                cascades = await self._detector.detect(propagation_id, hazard_type, intensity, zone_conditions)
            except Exception as e:
                log.warning(f"Error detecting cascades: {e}")

        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "propagation_id": propagation_id,
            "cascade_id": f"casc_{propagation_id}",
            "cascades": cascades,
            "latency_ms": latency_ms
        }

    async def build_domino_chain(self, hazard_type: str, intensity: float) -> dict[str, Any]:
        t0 = time.perf_counter()
        chain = {}
        probability = 0.0
        
        if self._builder and self._calculator:
            try:
                chain = await self._builder.build(hazard_type, intensity)
                probability = await self._calculator.calculate(chain)
            except Exception as e:
                log.warning(f"Error building domino chain: {e}")

        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "chain": chain,
            "probability": probability,
            "latency_ms": latency_ms
        }
