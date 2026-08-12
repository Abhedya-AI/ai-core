from __future__ import annotations
from .routes.models_router import router as models_router
from .routes.features_router import router as features_router
from .routes.monitoring_router import router as monitoring_router
from .routes.governance_router import router as governance_router
from .routes.security_router import router as security_router
from .routes.organizations_router import router as organizations_router
from .routes.plants_router import router as plants_router
from .routes.admin_router import router as admin_router
from .routes.analytics_router import router as analytics_router
from .routes.health_router import router as health_router
from .ws import ws_router

__all__ = [
    "models_router", "features_router", "monitoring_router", "governance_router",
    "security_router", "organizations_router", "plants_router", "admin_router",
    "analytics_router", "health_router", "ws_router"
]
