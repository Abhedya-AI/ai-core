"""
app/api/v1/root_cause.py — Root Cause Analysis Platform API gateway.

Aggregates all RCA module routers under the /rca prefix.
"""
from fastapi import APIRouter

from app.modules.root_cause.api.investigations_router import router as investigations_router
from app.modules.root_cause.api.evidence_router import router as evidence_router
from app.modules.root_cause.api.timeline_router import router as timeline_router
from app.modules.root_cause.api.hypotheses_router import router as hypotheses_router
from app.modules.root_cause.api.causal_graph_router import router as causal_graph_router
from app.modules.root_cause.api.recommendations_router import router as recommendations_router
from app.modules.root_cause.api.reports_router import router as reports_router
from app.modules.root_cause.api.ws import router as rca_ws_router

from app.modules.root_cause.api.memory_router import router as memory_router
from app.modules.root_cause.api.patterns_router import router as patterns_router
from app.modules.root_cause.api.context_router import router as context_router
from app.modules.root_cause.api.counterfactual_router import router as counterfactual_router
from app.modules.root_cause.api.lessons_router import router as lessons_router
from app.modules.root_cause.api.feedback_router import router as feedback_router
from app.modules.root_cause.api.explain_router import router as explain_router
from app.modules.root_cause.api.analytics_router import router as analytics_router
from app.modules.root_cause.api.intelligence_ws import router as intelligence_ws_router

router = APIRouter(prefix="/rca", tags=["Root Cause Analysis"])

router.include_router(investigations_router)
router.include_router(evidence_router)
router.include_router(timeline_router)
router.include_router(hypotheses_router)
router.include_router(causal_graph_router)
router.include_router(recommendations_router)
router.include_router(reports_router)
router.include_router(rca_ws_router)

router.include_router(memory_router)
router.include_router(patterns_router)
router.include_router(context_router)
router.include_router(counterfactual_router)
router.include_router(lessons_router)
router.include_router(feedback_router)
router.include_router(explain_router)
router.include_router(analytics_router)
router.include_router(intelligence_ws_router)
