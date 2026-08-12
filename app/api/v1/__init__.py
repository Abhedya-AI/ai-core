"""
app/api/v1/__init__.py — API v1 router aggregation.

All v1 routers are collected here and exposed as `api_v1_router`.
main.py mounts this once under /api/v1.
"""
from fastapi import APIRouter

# Existing routers
from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.emergency import router as emergency_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.rag import router as rag_router
from app.api.v1.root_cause import router as root_cause_router
from app.api.v1.sse import router as sse_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.agent import router as agent_router

# Sensor Intelligence routers
from app.api.v1.sensor_ai import router as sensor_ai_router
from app.api.v1.sensor_ai_ws import router as sensor_ai_ws_router
from app.api.v1.sensor_alerts import router as sensor_alerts_router
from app.api.v1.sensor_analytics import router as sensor_analytics_router
from app.api.v1.sensor_anomalies import router as sensor_anomalies_router
from app.api.v1.sensor_correlations import router as sensor_correlations_router
from app.api.v1.sensor_dashboard import router as sensor_dashboard_router
from app.api.v1.sensor_events import router as sensor_events_router
from app.api.v1.sensor_fleet import router as sensor_fleet_router
from app.api.v1.sensor_health import router as sensor_health_router
from app.api.v1.sensor_history import router as sensor_history_router
from app.api.v1.sensor_maintenance import router as sensor_maintenance_router
from app.api.v1.sensor_readings import router as sensor_readings_router
from app.api.v1.sensor_reports import router as sensor_reports_router
from app.api.v1.sensor_rules import router as sensor_rules_router
from app.api.v1.sensor_ws import router as sensor_ws_router
from app.api.v1.sensor_zones import router as sensor_zones_router
from app.api.v1.sensors import router as sensors_router

# Phase 4 Event-Driven Platform Routers
from app.api.v1.audit_api import router as audit_api_router
from app.api.v1.events_api import router as events_api_router
from app.api.v1.notifications_api import router as notifications_api_router
from app.api.v1.platform_ws import router as platform_ws_router
from app.api.v1.supervisor_api import router as supervisor_api_router
from app.api.v1.system_status_api import router as system_status_api_router

# Vision Intelligence Foundation (Sprint 6)
from app.api.v1.vision_alerts import router as vision_alerts_router
from app.api.v1.vision_cameras import router as vision_cameras_router
from app.api.v1.vision_detections import router as vision_detections_router
from app.api.v1.vision_frame_history import router as vision_frame_history_router
from app.api.v1.vision_streams import router as vision_streams_router
from app.api.v1.vision_tracking import router as vision_tracking_router
from app.api.v1.vision_ws import router as vision_ws_router

# Knowledge Graph Platform
from app.modules.knowledge.api.routes import router as knowledge_router
from app.modules.knowledge.api.ws import router as knowledge_ws_router

# Vision Safety Intelligence Engine (New Routers)
from app.modules.vision.api.analytics_router import router as vision_safety_analytics_router
from app.modules.vision.api.fall_detection_router import router as fall_detection_router
from app.modules.vision.api.fire_verification_router import router as fire_verification_router
from app.modules.vision.api.occupancy_router import router as occupancy_router
from app.modules.vision.api.ppe_router import router as ppe_router
from app.modules.vision.api.restricted_zones_router import router as restricted_zones_router
from app.modules.vision.api.violations_router import router as vision_violations_router
from app.modules.vision.api.vision_ai_router import router as vision_ai_router
from app.modules.vision.api.worker_interactions_router import router as worker_interactions_router
from app.modules.vision.api.ws import router as vision_safety_ws_router

# Predictive Risk Intelligence Platform (Sprint 8)
from app.modules.risk_prediction.api.routes import router as risk_router
from app.modules.risk_prediction.api.ws import ws_router as risk_ws_router

api_v1_router = APIRouter()

# Auth
api_v1_router.include_router(auth_router)

# Business domain
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(analytics_router)

# Phase 4 Platform Routers
api_v1_router.include_router(events_api_router)
api_v1_router.include_router(supervisor_api_router)
api_v1_router.include_router(notifications_api_router)
api_v1_router.include_router(audit_api_router)
api_v1_router.include_router(system_status_api_router)
api_v1_router.include_router(platform_ws_router)

# Knowledge Graph Platform Engine
api_v1_router.include_router(knowledge_router)
api_v1_router.include_router(knowledge_ws_router)

# Vision Safety Intelligence Engine Routers
api_v1_router.include_router(ppe_router)
api_v1_router.include_router(vision_violations_router)
api_v1_router.include_router(restricted_zones_router)
api_v1_router.include_router(vision_safety_analytics_router)
api_v1_router.include_router(occupancy_router)
api_v1_router.include_router(worker_interactions_router)
api_v1_router.include_router(fall_detection_router)
api_v1_router.include_router(fire_verification_router)
api_v1_router.include_router(vision_ai_router)
api_v1_router.include_router(vision_safety_ws_router)

# Legacy Sprint 3
api_v1_router.include_router(emergency_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(root_cause_router)
api_v1_router.include_router(agent_router)

# Health checks
api_v1_router.include_router(health_router)

# Real-time streaming (WebSocket & SSE)
api_v1_router.include_router(ws_router)
api_v1_router.include_router(sse_router)

# ── Sensor Intelligence ────────────────────────────────────────────────────────
api_v1_router.include_router(sensors_router)
api_v1_router.include_router(sensor_readings_router)
api_v1_router.include_router(sensor_anomalies_router)
api_v1_router.include_router(sensor_analytics_router)
api_v1_router.include_router(sensor_rules_router)
api_v1_router.include_router(sensor_correlations_router)
api_v1_router.include_router(sensor_health_router)
api_v1_router.include_router(sensor_alerts_router)
api_v1_router.include_router(sensor_history_router)
api_v1_router.include_router(sensor_zones_router)
api_v1_router.include_router(sensor_ws_router)
api_v1_router.include_router(sensor_reports_router)
api_v1_router.include_router(sensor_dashboard_router)
api_v1_router.include_router(sensor_fleet_router)
api_v1_router.include_router(sensor_maintenance_router)
api_v1_router.include_router(sensor_events_router)
api_v1_router.include_router(sensor_ai_router)
api_v1_router.include_router(sensor_ai_ws_router)

# ── Vision Intelligence Foundation ─────────────────────────────────────────────
api_v1_router.include_router(vision_cameras_router)
api_v1_router.include_router(vision_streams_router)
api_v1_router.include_router(vision_detections_router)
api_v1_router.include_router(vision_tracking_router)
api_v1_router.include_router(vision_frame_history_router)
api_v1_router.include_router(vision_alerts_router)
api_v1_router.include_router(vision_ws_router)

# ── Predictive Risk Intelligence Platform (Sprint 8) ───────────────────────────
api_v1_router.include_router(risk_router)
api_v1_router.include_router(risk_ws_router)

# ── Forecast Intelligence Platform (Sprint 9) ──────────────────────────────────
from app.modules.forecast.api.routes import router as forecast_router
from app.modules.forecast.api.ws import ws_router as forecast_ws_router

api_v1_router.include_router(forecast_router)
api_v1_router.include_router(forecast_ws_router)

# ── Hazard Propagation Intelligence Platform (Sprint 10) ───────────────────────
try:
    from app.modules.hazard_propagation.api.routes import router as hazard_router
    from app.modules.hazard_propagation.api.ws import ws_router as hazard_ws_router

    api_v1_router.include_router(hazard_router)
    api_v1_router.include_router(hazard_ws_router)
except Exception as _hazard_import_err:  # pragma: no cover
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Hazard Propagation routers not yet available: %s", _hazard_import_err
    )

# ── Digital Twin & Simulation Intelligence Platform (Sprint 11) ────────────────
try:
    from app.modules.digital_twin.api.routes import router as twin_router
    from app.modules.digital_twin.api.ws import ws_router as twin_ws_router

    api_v1_router.include_router(twin_router)
    api_v1_router.include_router(twin_ws_router)
except Exception as _twin_import_err:  # pragma: no cover
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Digital Twin routers not yet available: %s", _twin_import_err
    )

# ── Enterprise Production Platform (Sprint 12) ─────────────────────────────────
try:
    from app.modules.platform.api.routes.models_router import router as platform_models_router
    from app.modules.platform.api.routes.features_router import router as platform_features_router
    from app.modules.platform.api.routes.monitoring_router import router as platform_monitoring_router
    from app.modules.platform.api.routes.governance_router import router as platform_governance_router
    from app.modules.platform.api.routes.security_router import router as platform_security_router
    from app.modules.platform.api.routes.organizations_router import router as platform_organizations_router
    from app.modules.platform.api.routes.plants_router import router as platform_plants_router
    from app.modules.platform.api.routes.admin_router import router as platform_admin_router
    from app.modules.platform.api.routes.analytics_router import router as platform_analytics_router
    from app.modules.platform.api.routes.health_router import router as platform_health_router
    from app.modules.platform.api.ws import ws_router as platform_ws_router

    api_v1_router.include_router(platform_models_router)
    api_v1_router.include_router(platform_features_router)
    api_v1_router.include_router(platform_monitoring_router)
    api_v1_router.include_router(platform_governance_router)
    api_v1_router.include_router(platform_security_router)
    api_v1_router.include_router(platform_organizations_router)
    api_v1_router.include_router(platform_plants_router)
    api_v1_router.include_router(platform_admin_router)
    api_v1_router.include_router(platform_analytics_router)
    api_v1_router.include_router(platform_health_router)
    api_v1_router.include_router(platform_ws_router)
except Exception as _platform_import_err:  # pragma: no cover
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Enterprise Platform routers not yet available: %s", _platform_import_err
    )

__all__ = ["api_v1_router"]
