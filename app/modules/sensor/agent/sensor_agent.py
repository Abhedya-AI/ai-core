"""
sensor/agent/sensor_agent.py — Sensor Intelligence Domain Agent.

Consumes sensor readings from AgentContext or direct dict payload,
runs multi-engine anomaly detection + threshold policy evaluation,
updates sensor health FSM, computes digital twin state, and outputs
an AgentResult with typed domain events and evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult, AgentTelemetry
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.sensor.analysis.engine_registry import AnomalyEngineRegistry
from app.modules.sensor.application.health_tracker import SensorHealthTracker
from app.modules.sensor.application.policy_engine import ThresholdPolicyEngine
from app.modules.sensor.application.telemetry_buffer import TelemetryBuffer
from app.modules.sensor.domain.events import (
    anomaly_detected_event,
    health_changed_event,
)
from app.modules.sensor.domain.models import SensorAnomaly, SensorReading, SensorHealthState
from app.modules.sensor.agent.sensor_result import SensorAgentResult

log = get_logger("agents.sensor")


class SensorAgent(BaseAgent):
    """
    Sensor Intelligence Agent.

    Evaluates live or batch telemetry, flags anomalies, updates health states,
    enforces threshold policies, and emits structured safety evidence.
    """

    name: str = "SensorAgent"
    description: str = "Ingests, analyzes, and assesses industrial sensor streams."

    def __init__(
        self,
        buffer: TelemetryBuffer | None = None,
        health_tracker: SensorHealthTracker | None = None,
        engine_registry: AnomalyEngineRegistry | None = None,
        policy_engine: ThresholdPolicyEngine | None = None,
    ):
        super().__init__()
        self.buffer = buffer or TelemetryBuffer()
        self.health_tracker = health_tracker or SensorHealthTracker()
        self.engine_registry = engine_registry or AnomalyEngineRegistry()
        self.policy_engine = policy_engine or ThresholdPolicyEngine()

    async def can_handle(self, context: AgentContext | dict[str, Any]) -> bool:
        """Determines if this agent should handle the given task or payload."""
        if isinstance(context, dict):
            intent = str(context.get("intent", "")).upper()
            if intent in ("SENSOR_INTELLIGENCE", "TELEMETRY", "SENSOR_ANOMALY", "SENSOR"):
                return True
            if "sensor_id" in context or "readings" in context or "sensor_data" in context:
                return True
            return False

        if not isinstance(context, AgentContext):
            return False

        if context.intent and context.intent.upper() in ("SENSOR_INTELLIGENCE", "TELEMETRY", "SENSOR_ANOMALY", "SENSOR"):
            return True

        if context.sensor_data:
            return True

        q = context.query.lower()
        keywords = ("sensor", "telemetry", "psi", "celsius", "fahrenheit", "reading", "vibration", "pressure", "flow", "temperature")
        return any(kw in q for kw in keywords)

    async def run(self, input_data: dict[str, Any]) -> SensorAgentResult:
        """Direct dict execution interface."""
        ctx = AgentContext(
            query=input_data.get("query", "Analyze sensor data"),
            intent=input_data.get("intent", "SENSOR_INTELLIGENCE"),
            sensor_data=input_data.get("sensor_data", [input_data] if "sensor_id" in input_data else [])
        )
        res = await self._run(ctx)
        if isinstance(res, SensorAgentResult):
            return res
        return SensorAgentResult(
            agent_name=self.name,
            success=res.success,
            confidence=res.confidence,
            evidence=res.evidence,
            recommendations=res.recommendations,
            events=res.events,
            output_data=res.output_data
        )

    async def _run(self, context: AgentContext) -> AgentResult:
        """Execute the full sensor intelligence pipeline."""
        raw_data = context.sensor_data or []
        if not raw_data and hasattr(context, "data") and context.data:
            if isinstance(context.data, dict) and ("sensor_id" in context.data or "value" in context.data):
                raw_data = [context.data]

        log.info(f"SensorAgent processing {len(raw_data)} sensor reading(s)")

        all_anomalies: list[SensorAnomaly] = []
        health_changes: list[dict] = []
        threshold_violations: list[dict] = []
        processed_health: dict[str, SensorHealthState] = {}

        # 1. Convert raw dicts → SensorReading, push to buffer
        for item in raw_data:
            sensor_id = str(item.get("sensor_id", ""))
            if not sensor_id:
                continue

            reading = SensorReading(
                sensor_id=sensor_id,
                value=float(item.get("value", 0.0)),
                unit=str(item.get("unit", "")),
                timestamp=item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                quality_score=float(item.get("quality_score", 1.0)),
                metadata={
                    k: v for k, v in item.items()
                    if k not in ("sensor_id", "value", "unit", "timestamp", "quality_score")
                },
            )
            self.buffer.push(reading)

            # 2. Get history for statistical analysis
            history = self.buffer.get_values(sensor_id)

            # 3. Run multi-engine anomaly detection
            anomalies = self.engine_registry.analyze_reading(reading, history)
            all_anomalies.extend(anomalies)

            # 4. Run threshold policy evaluation
            policy_anomalies = self.policy_engine.evaluate(reading, history)
            for pa in policy_anomalies:
                all_anomalies.append(pa)
                threshold_violations.append({
                    "sensor_id": sensor_id,
                    "value": reading.value,
                    "anomaly_type": pa.anomaly_type.value,
                    "severity": pa.severity.value,
                    "description": pa.description,
                })

            # 5. Update health state machine
            state, previous_status = self.health_tracker.update(
                sensor_id, reading, anomalies,
            )
            processed_health[sensor_id] = state
            if previous_status:
                health_changes.append({
                    "sensor_id": sensor_id,
                    "from": previous_status.value,
                    "to": state.status.value,
                })

        # 6. Aggregate assessment
        health_states = list(processed_health.values())
        total_sensors = len(health_states) or 1
        healthy_count = sum(1 for h in health_states if h.status.value == "HEALTHY")
        fleet_health_pct = (healthy_count / total_sensors) * 100.0
        recs = []
        if any(a.severity.value == "CRITICAL" for a in all_anomalies):
            recs.append("Immediate inspection required for critical sensors.")

        # 7. Generate domain events & recommendations
        events: list[object] = []

        for anomaly in all_anomalies:
            events.append(anomaly_detected_event(
                anomaly=anomaly,
                trace_id=context.trace_id,
            ))

        for hc in health_changes:
            events.append(health_changed_event(
                sensor_id=hc["sensor_id"],
                previous_status=hc["from"],
                new_status=hc["to"],
                reason="State machine transition",
                trace_id=context.trace_id,
            ))

        evidence = [
            f"Processed {len(raw_data)} sensor reading(s)",
            f"Detected {len(all_anomalies)} anomaly(ies) across {len(set(a.sensor_id for a in all_anomalies))} sensor(s)",
            f"Fleet health: {fleet_health_pct:.1f}%",
        ]
        if threshold_violations:
            evidence.append(f"{len(threshold_violations)} threshold violation(s) detected")

        output_data = {
            "readings_count": len(raw_data),
            "anomaly_count": len(all_anomalies),
            "anomalies": [a.model_dump() for a in all_anomalies],
            "fleet_health_pct": fleet_health_pct,
            "health_states": {k: v.status.value for k, v in processed_health.items()},
        }

        return SensorAgentResult(
            agent_name=self.name,
            success=True,
            confidence=fleet_health_pct / 100.0,
            evidence=evidence,
            recommendations=recs,
            events=events,
            output_data=output_data,
            telemetry=AgentTelemetry(
                agent_name=self.name,
                confidence=fleet_health_pct / 100.0,
                events_published=len(events),
            ),
        )
