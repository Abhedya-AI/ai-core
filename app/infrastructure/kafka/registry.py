"""
kafka/registry.py — Kafka topic name constants.

All topic names are defined here. No topic name strings should appear
anywhere else in the codebase.

Convention:
  {domain}.{entity}.{action}

Examples:
  sensor.reading.created
  risk.prediction.completed
  emergency.alert.triggered
  worker.status.updated
"""


class Topics:
    """Kafka topic name constants for ABHEDYA."""

    # ── Sensor Domain ──────────────────────────────────────────────────────────
    SENSOR_READING_CREATED = "sensor.reading.created"
    SENSOR_ANOMALY_DETECTED = "sensor.anomaly.detected"

    # ── Risk Domain ────────────────────────────────────────────────────────────
    RISK_PREDICTION_COMPLETED = "risk.prediction.completed"
    RISK_THRESHOLD_BREACHED = "risk.threshold.breached"

    # ── Emergency Domain ───────────────────────────────────────────────────────
    EMERGENCY_ALERT_TRIGGERED = "emergency.alert.triggered"
    EMERGENCY_RESPONSE_DISPATCHED = "emergency.response.dispatched"

    # ── Worker Domain ──────────────────────────────────────────────────────────
    WORKER_STATUS_UPDATED = "worker.status.updated"
    WORKER_PROXIMITY_ALERT = "worker.proximity.alert"

    # ── Knowledge Graph Domain ────────────────────────────────────────────────
    GRAPH_NODE_CREATED = "graph.node.created"
    GRAPH_RELATIONSHIP_CREATED = "graph.relationship.created"

    # ── Agent Domain ──────────────────────────────────────────────────────────
    AGENT_TASK_REQUESTED = "agent.task.requested"
    AGENT_TASK_COMPLETED = "agent.task.completed"

    # ── Root Cause Domain ─────────────────────────────────────────────────────
    ROOT_CAUSE_ANALYSIS_COMPLETED = "root_cause.analysis.completed"

    @classmethod
    def all_topics(cls) -> list[str]:
        """Return all defined topic names."""
        return [
            v for k, v in vars(cls).items()
            if not k.startswith("_") and isinstance(v, str)
        ]
