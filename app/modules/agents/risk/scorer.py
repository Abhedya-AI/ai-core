"""scorer.py — Deterministic Risk Scoring Engine."""

from app.modules.agents.risk.models import PriorityEnum, RiskEvidence, RiskScore, SeverityEnum


class RiskScorer:
    """Calculates deterministic probability, severity, impact, and priority from gathered evidence."""

    @staticmethod
    def compute_score(evidence: RiskEvidence, target_id: str | None = None) -> RiskScore:
        """
        Compute deterministic risk score.

        Returns:
            RiskScore object containing probability, severity, impact, priority, and confidence.
        """
        base_probability = 0.2
        confidence = 0.95

        # Factor 1: Sensor Anomalies
        sensor_anomaly_count = 0
        for sensor in evidence.sensor_readings:
            val = float(sensor.get("value", 0.0))
            thresh = float(sensor.get("threshold", 100.0))
            if val > thresh:
                sensor_anomaly_count += 1
        base_probability += min(0.4, sensor_anomaly_count * 0.2)

        # Factor 2: Maintenance Overdue
        overdue_count = sum(1 for m in evidence.maintenance_logs if m.get("overdue", False))
        base_probability += min(0.2, overdue_count * 0.1)

        # Factor 3: Vision Anomalies (e.g. Smoke/Fire/PPE)
        if evidence.vision_events:
            base_probability += 0.25

        probability = min(0.99, max(0.05, round(base_probability, 2)))

        # Impact Calculation (Scale 0-100)
        impact = round(probability * 100.0, 1)

        # Severity & Priority Matrix
        if impact >= 85.0:
            severity = SeverityEnum.CRITICAL
            priority = PriorityEnum.P1
        elif impact >= 65.0:
            severity = SeverityEnum.HIGH
            priority = PriorityEnum.P2
        elif impact >= 40.0:
            severity = SeverityEnum.MEDIUM
            priority = PriorityEnum.P3
        else:
            severity = SeverityEnum.LOW
            priority = PriorityEnum.P4

        return RiskScore(
            probability=probability,
            severity=severity,
            confidence=confidence,
            impact=impact,
            priority=priority,
            score_value=impact,
        )
