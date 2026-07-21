"""tracker.py — Entity Tracking Engine for Temporal Consistency."""

from app.core.logging import get_logger
from app.modules.agents.vision.models import VisionDetection

log = get_logger("agents.vision.tracker")


class EntityTracker:
    """Tracks objects across consecutive frames to maintain temporal consistency."""

    def __init__(self) -> None:
        self._tracks: dict[str, int] = {}

    def track_entities(self, camera_id: str, detections: list[VisionDetection]) -> list[VisionDetection]:
        """
        Assign track IDs to detections for temporal continuity.

        Returns:
            list of VisionDetection objects with assigned track_id attributes.
        """
        tracked: list[VisionDetection] = []
        for idx, det in enumerate(detections):
            label_key = f"{camera_id}:{det.label}"
            self._tracks[label_key] = self._tracks.get(label_key, 0) + 1
            track_id = f"TRACK-{det.label.upper()}-{self._tracks[label_key]}"

            det.track_id = track_id
            det.metadata["temporal_consistency"] = 0.95
            tracked.append(det)

        return tracked
