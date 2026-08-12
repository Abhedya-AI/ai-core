"""
api/__init__.py — Vision Safety API Package Exports.
"""
from app.modules.vision.api.analytics_router import router as vision_analytics_router
from app.modules.vision.api.fall_detection_router import router as fall_detection_router
from app.modules.vision.api.fire_verification_router import router as fire_verification_router
from app.modules.vision.api.occupancy_router import router as occupancy_router
from app.modules.vision.api.ppe_router import router as ppe_router
from app.modules.vision.api.restricted_zones_router import router as restricted_zones_router
from app.modules.vision.api.violations_router import router as violations_router
from app.modules.vision.api.vision_ai_router import router as vision_ai_router
from app.modules.vision.api.worker_interactions_router import router as worker_interactions_router
from app.modules.vision.api.ws import router as vision_safety_ws_router

__all__ = [
    "ppe_router",
    "violations_router",
    "restricted_zones_router",
    "vision_analytics_router",
    "occupancy_router",
    "worker_interactions_router",
    "fall_detection_router",
    "fire_verification_router",
    "vision_ai_router",
    "vision_safety_ws_router",
]
