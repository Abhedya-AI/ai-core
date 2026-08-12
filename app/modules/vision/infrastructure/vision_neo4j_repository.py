"""
vision/infrastructure/vision_neo4j_repository.py — Vision Knowledge Graph Repository.

Provides Cypher-based write and read operations to synchronize Vision
entities (Camera, Detection, Frame, TrackingObject, VisionAlert) into
the Neo4j Knowledge Graph.
"""
from __future__ import annotations
import logging
from app.core.logging import get_logger
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.detection_event import DetectionEvent
from app.modules.vision.domain.entities.frame import Frame
from app.modules.vision.domain.entities.tracking_object import TrackingObject
from app.modules.vision.domain.entities.vision_alert import VisionAlert

log = get_logger("vision.infrastructure.neo4j")

class VisionNeo4jRepository:
    def __init__(self) -> None:
        self._driver = None
        self._use_neo4j = False

    def _connect(self) -> bool:
        if self._driver is not None:
            return True
        try:
            from neo4j import AsyncGraphDatabase
            from app.core.config.settings import get_settings
            settings = get_settings()
            uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
            user = getattr(settings, 'NEO4J_USER', 'neo4j')
            password = getattr(settings, 'NEO4J_PASSWORD', 'password')
            self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
            self._use_neo4j = True
            return True
        except Exception as exc:
            log.warning(f"Neo4j unavailable for Vision KG sync: {exc}")
            return False

    async def _run_query(self, cypher: str, params: dict) -> list[dict]:
        if not self._connect():
            return []
        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, params)
                records = await result.data()
                return records
        except Exception as exc:
            log.warning(f"Neo4j query failed: {exc}")
            return []

    async def upsert_camera_node(self, camera: Camera) -> bool:
        cypher = """
        MERGE (c:Camera {id: $id})
        SET c.name = $name, c.type = $type, c.location = $location,
            c.zone_id = $zone_id, c.plant_id = $plant_id, c.status = $status,
            c.is_active = $is_active, c.updated_at = $updated_at
        WITH c
        WHERE $zone_id IS NOT NULL
        MERGE (z:Zone {id: $zone_id})
        MERGE (c)-[:MONITORS]->(z)
        """
        params = {
            "id": camera.id,
            "name": camera.name,
            "type": camera.camera_type.value if hasattr(camera.camera_type, 'value') else camera.camera_type,
            "location": camera.location,
            "zone_id": camera.zone_id,
            "plant_id": camera.plant_id,
            "status": camera.status.value if hasattr(camera.status, 'value') else camera.status,
            "is_active": camera.is_active,
            "updated_at": camera.updated_at.isoformat() if camera.updated_at else None
        }
        await self._run_query(cypher, params)
        return True

    async def upsert_detection_node(self, detection_event: DetectionEvent) -> bool:
        cypher = """
        MERGE (d:Detection {id: $id})
        SET d.hazard_type = $hazard_type, d.confidence = $confidence,
            d.risk_level = $risk_level, d.risk_score = $risk_score,
            d.detected_at = $detected_at, d.is_violation = $is_violation,
            d.camera_id = $camera_id
        WITH d
        MATCH (c:Camera {id: $camera_id})
        MERGE (d)-[:DETECTED_AT]->(c)
        WITH d
        WHERE $zone_id IS NOT NULL
        MERGE (z:Zone {id: $zone_id})
        MERGE (d)-[:LOCATED_IN]->(z)
        """
        params = {
            "id": detection_event.detection_id,
            "hazard_type": detection_event.hazard_type.value if hasattr(detection_event.hazard_type, 'value') else detection_event.hazard_type,
            "confidence": detection_event.confidence,
            "risk_level": detection_event.risk_level.value if hasattr(detection_event.risk_level, 'value') else detection_event.risk_level,
            "risk_score": detection_event.risk_score,
            "detected_at": detection_event.detected_at.isoformat() if detection_event.detected_at else None,
            "is_violation": detection_event.is_ppe_violation,
            "camera_id": detection_event.camera_id,
            "zone_id": detection_event.zone_id
        }
        await self._run_query(cypher, params)
        
        if detection_event.is_ppe_violation or params['hazard_type'] in ('FIRE', 'FALL'):
            worker_cypher = """
            MATCH (d:Detection {id: $id})
            MERGE (w:Worker {id: $track_id})
            MERGE (d)-[:ASSOCIATED_WITH]->(w)
            """
            worker_params = {"id": detection_event.detection_id, "track_id": detection_event.track_id or "UNKNOWN"}
            await self._run_query(worker_cypher, worker_params)
            
        return True

    async def upsert_frame_node(self, frame: Frame) -> bool:
        cypher = """
        MERGE (f:Frame {id: $id})
        SET f.camera_id = $camera_id, f.captured_at = $captured_at,
            f.sequence_number = $sequence_number, f.zone_id = $zone_id
        WITH f
        MATCH (c:Camera {id: $camera_id})
        MERGE (f)-[:CAPTURED_BY]->(c)
        """
        params = {
            "id": frame.frame_id,
            "camera_id": frame.camera_id,
            "captured_at": frame.timestamp.isoformat() if frame.timestamp else None,
            "sequence_number": frame.sequence_number,
            "zone_id": frame.zone_id
        }
        await self._run_query(cypher, params)
        return True

    async def upsert_tracking_node(self, track: TrackingObject) -> bool:
        cypher = """
        MERGE (t:TrackingObject {id: $id})
        SET t.object_class = $object_class, t.camera_id = $camera_id,
            t.zone_id = $zone_id, t.first_seen = $first_seen,
            t.last_seen = $last_seen, t.is_active = $is_active
        WITH t
        MATCH (c:Camera {id: $camera_id})
        MERGE (t)-[:TRACKED_BY]->(c)
        """
        params = {
            "id": track.track_id,
            "object_class": track.object_class,
            "camera_id": track.camera_id,
            "zone_id": track.zone_id,
            "first_seen": track.first_seen.isoformat() if track.first_seen else None,
            "last_seen": track.last_seen.isoformat() if track.last_seen else None,
            "is_active": track.is_active
        }
        await self._run_query(cypher, params)
        
        if hasattr(track, 'zone_crossings') and track.zone_crossings:
            for crossing in track.zone_crossings:
                cross_cypher = """
                MATCH (t:TrackingObject {id: $track_id})
                MERGE (z:Zone {id: $zone_id})
                MERGE (t)-[r:ENTERED {time: $time}]->(z)
                """
                cross_params = {
                    "track_id": track.track_id,
                    "zone_id": crossing.zone_id,
                    "time": crossing.timestamp.isoformat() if crossing.timestamp else None
                }
                await self._run_query(cross_cypher, cross_params)
        return True

    async def upsert_alert_node(self, alert: VisionAlert) -> bool:
        cypher = """
        MERGE (a:VisionAlert {id: $id})
        SET a.alert_type = $alert_type, a.severity = $severity,
            a.status = $status, a.created_at = $created_at,
            a.camera_id = $camera_id
        WITH a
        WHERE $zone_id IS NOT NULL
        MERGE (z:Zone {id: $zone_id})
        MERGE (a)-[:IN_ZONE]->(z)
        """
        params = {
            "id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity.value if hasattr(alert.severity, 'value') else alert.severity,
            "status": alert.status.value if hasattr(alert.status, 'value') else alert.status,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "camera_id": alert.camera_id,
            "zone_id": alert.zone_id
        }
        await self._run_query(cypher, params)
        return True

    async def link_camera_group(self, camera_id_1: str, camera_id_2: str) -> bool:
        cypher = """
        MERGE (c1:Camera {id: $c1})
        MERGE (c2:Camera {id: $c2})
        MERGE (c1)-[:CONNECTED_TO]->(c2)
        """
        await self._run_query(cypher, {"c1": camera_id_1, "c2": camera_id_2})
        return True

    async def get_cameras_in_zone(self, zone_id: str) -> list[dict]:
        cypher = "MATCH (c:Camera)-[:MONITORS]->(z:Zone {id: $zone_id}) RETURN c"
        return await self._run_query(cypher, {"zone_id": zone_id})

    async def get_recent_detections_for_zone(self, zone_id: str, limit: int = 20) -> list[dict]:
        cypher = """
        MATCH (d:Detection)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
        RETURN d ORDER BY d.detected_at DESC LIMIT $limit
        """
        return await self._run_query(cypher, {"zone_id": zone_id, "limit": limit})

    async def get_camera_context(self, camera_id: str) -> dict:
        cam_cypher = "MATCH (c:Camera {id: $camera_id}) RETURN c"
        zone_cypher = "MATCH (c:Camera {id: $camera_id})-[:MONITORS]->(z:Zone) RETURN z"
        det_cypher = "MATCH (d:Detection)-[:DETECTED_AT]->(c:Camera {id: $camera_id}) RETURN d ORDER BY d.detected_at DESC LIMIT 5"
        alerts_cypher = "MATCH (a:VisionAlert {camera_id: $camera_id}) WHERE a.status = 'ACTIVE' RETURN a"
        
        cams = await self._run_query(cam_cypher, {"camera_id": camera_id})
        zones = await self._run_query(zone_cypher, {"camera_id": camera_id})
        dets = await self._run_query(det_cypher, {"camera_id": camera_id})
        alerts = await self._run_query(alerts_cypher, {"camera_id": camera_id})
        
        return {
            "camera": cams[0]["c"] if cams else {},
            "zone": zones[0]["z"] if zones else {},
            "recent_detections": [d["d"] for d in dets],
            "active_alerts": [a["a"] for a in alerts]
        }

    async def get_zone_risk_summary(self, zone_id: str) -> dict:
        det_cypher = """
        MATCH (d:Detection)-[:LOCATED_IN]->(z:Zone {id: $zone_id})
        WHERE d.risk_level IN ['CRITICAL', 'HIGH']
        RETURN d.risk_level as level, count(d) as c
        """
        alert_cypher = """
        MATCH (a:VisionAlert)-[:IN_ZONE]->(z:Zone {id: $zone_id})
        WHERE a.status = 'ACTIVE'
        RETURN count(a) as c
        """
        dets = await self._run_query(det_cypher, {"zone_id": zone_id})
        alerts = await self._run_query(alert_cypher, {"zone_id": zone_id})
        
        critical = sum([d['c'] for d in dets if d['level'] == 'CRITICAL'])
        high = sum([d['c'] for d in dets if d['level'] == 'HIGH'])
        active_alerts = alerts[0]['c'] if alerts else 0
        
        return {
            "zone_id": zone_id,
            "critical_detection_count": critical,
            "high_detection_count": high,
            "active_alert_count": active_alerts,
            "risk_level": "CRITICAL" if critical > 0 or active_alerts > 0 else "HIGH" if high > 0 else "NORMAL"
        }
