"""
vision_agent.py — Master Vision Intelligence Agent.

Converts visual observations from CCTV, drones, and video streams into structured domain events.
"""

from app.core.logging import get_logger
from app.modules.agents.core.agent_context import AgentContext
from app.modules.agents.core.agent_result import AgentResult
from app.modules.agents.core.base_agent import BaseAgent
from app.modules.agents.core.types import Capability
from app.modules.agents.vision.confidence import ConfidenceEngine
from app.modules.agents.vision.detector import ObjectDetector
from app.modules.agents.vision.events import VisionEventGenerator
from app.modules.agents.vision.fire import FireModule
from app.modules.agents.vision.fusion import DetectionFusionEngine
from app.modules.agents.vision.models import VisionAgentResult
from app.modules.agents.vision.occupancy import OccupancyModule
from app.modules.agents.vision.ocr import OCRModule
from app.modules.agents.vision.ppe import PPEModule
from app.modules.agents.vision.smoke import SmokeModule
from app.modules.agents.vision.spill import SpillModule
from app.modules.agents.vision.tracker import EntityTracker

log = get_logger("agents.vision.orchestrator")


class VisionAgent(BaseAgent):
    """
    Master Vision Intelligence Agent.

    Orchestrates:
      Camera Stream -> Object Detector -> Tracker -> Specialized Modules (PPE/Fire/Smoke/Spill/Occupancy/OCR) -> Fusion -> Confidence Engine -> Event Generation.
    """

    name: str = "VisionAgent"
    version: str = "1.0.0"
    description: str = "Evaluates CCTV video streams, PPE compliance, and visual hazard detections."
    capabilities: list[Capability] = [Capability.VISION]

    def __init__(self) -> None:
        super().__init__()
        self.detector = ObjectDetector()
        self.tracker = EntityTracker()

    async def can_handle(self, context: AgentContext) -> bool:
        return "vision" in context.query.lower() or "camera" in context.query.lower() or "cctv" in context.query.lower()

    async def _run(self, context: AgentContext) -> AgentResult:
        camera_id = context.metadata.get("camera_id", "CAM-01")
        zone_id = context.zone_id or "ZONE-A"
        frame_input = context.metadata.get("detections") or context.vision_events

        # 1. Object Detection Inference
        raw_detections = self.detector.detect_objects(frame_input, camera_id=camera_id)

        # 2. Entity Tracking for Temporal Consistency
        tracked_detections = self.tracker.track_entities(camera_id, raw_detections)

        # 3. Modular Safety Evaluations
        ppe_violations = PPEModule.evaluate_compliance(tracked_detections)
        fire_detections = FireModule.detect_fire(tracked_detections)
        smoke_detections = SmokeModule.detect_smoke(tracked_detections)
        spill_detections = SpillModule.detect_spills(tracked_detections)
        occupancy_info = OccupancyModule.evaluate_occupancy(zone_id, tracked_detections)
        ocr_tags = OCRModule.extract_ocr_tags(tracked_detections, context.metadata)

        # 4. Multi-Camera & Sensor Fusion
        camera_map = {camera_id: tracked_detections}
        if "secondary_camera_id" in context.metadata:
            camera_map[context.metadata["secondary_camera_id"]] = tracked_detections
        agreement_score = DetectionFusionEngine.fuse_multi_camera(camera_map, context.sensor_data)

        # 5. Operational Confidence Computation
        confidence_metrics = ConfidenceEngine.compute_confidence(tracked_detections, agreement_score)

        # 6. Domain Event Generation
        events = VisionEventGenerator.generate_events(
            agent_name=self.name,
            camera_id=camera_id,
            zone_id=zone_id,
            detections=tracked_detections,
            confidence=confidence_metrics,
            trace_id=context.trace_id,
        )

        anomalies = [f"Detected {len(tracked_detections)} object(s) on camera '{camera_id}'"]
        if ppe_violations:
            anomalies.extend(ppe_violations)
        if fire_detections:
            anomalies.append(f"Active flame/fire detected on '{camera_id}'!")
        if smoke_detections:
            anomalies.append(f"Early smoke plume detected on '{camera_id}'!")
        if spill_detections:
            anomalies.append(f"Liquid/chemical spill detected on '{camera_id}'!")

        recs = ["Inspect target camera feed for visual confirmation"]
        if ppe_violations:
            recs.append("Issue safety compliance alert to non-compliant workers")
        if fire_detections or smoke_detections:
            recs.append("Initiate automatic thermal/smoke inspection in zone")

        return VisionAgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence_metrics.operational_confidence,
            evidence=anomalies,
            recommendations=recs,
            events=events,
            visual_anomalies=anomalies,
            zone_occupancy=occupancy_info,
            ppe_violations=ppe_violations,
            ocr_tags=ocr_tags,
            output_data={
                "camera_id": camera_id,
                "zone_id": zone_id,
                "detection_count": len(tracked_detections),
                "occupancy": occupancy_info,
                "confidence": confidence_metrics.model_dump(),
            },
            explanation=f"Vision Agent processed visual stream from camera '{camera_id}' in '{zone_id}'. Found {len(anomalies)} observation(s).",
        )
