"""timeline.py — Phase 2: Chronological Timeline Reconstruction Engine."""

from app.modules.agents.root_cause.models import EvidenceBundle, TimelineEvent


class TimelineReconstructor:
    """Phase 2: Reconstructs a chronological sequence of events preceding the incident."""

    @staticmethod
    def reconstruct_timeline(bundle: EvidenceBundle) -> list[TimelineEvent]:
        """
        Reconstruct timeline events sorted chronologically.

        Returns:
            list of TimelineEvent objects.
        """
        events: list[TimelineEvent] = []

        # 1. Telemetry anomalies
        for idx, s in enumerate(bundle.sensor_timeline):
            events.append(
                TimelineEvent(
                    timestamp=s.get("timestamp", f"08:{10 + idx}"),
                    event_label=f"Sensor '{s.get('sensor_id')}' threshold anomaly ({s.get('reading')})",
                    source="SENSOR",
                    entity_id=s.get("sensor_id", "SENSOR-1"),
                    details=s,
                )
            )

        # 2. Visual detections
        for idx, v in enumerate(bundle.vision_detections):
            events.append(
                TimelineEvent(
                    timestamp=v.get("timestamp", f"08:{15 + idx}"),
                    event_label=f"Visual detection: {v.get('detection')} on {v.get('camera_id')}",
                    source="VISION",
                    entity_id=v.get("camera_id", "CAM-01"),
                    details=v,
                )
            )

        # 3. Maintenance logs
        for m in bundle.maintenance_records:
            events.append(
                TimelineEvent(
                    timestamp="08:00 (Pre-Incident)",
                    event_label=f"Maintenance overdue by {m.get('overdue_days', 0)} days on {m.get('asset', 'Asset')}",
                    source="MAINTENANCE",
                    entity_id=m.get("asset", "ASSET-1"),
                    details=m,
                )
            )

        # Sort timeline
        events.sort(key=lambda x: x.timestamp)
        return events
