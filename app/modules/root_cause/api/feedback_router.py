from fastapi import APIRouter, Depends, Request, Query, HTTPException
from pydantic import BaseModel
from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger
from app.modules.root_cause.domain.models import FeedbackOutcome
from app.modules.root_cause.feedback.recommendation_feedback import RecommendationFeedbackTracker

log = get_logger("root_cause.api.feedback")
router = APIRouter()

class FeedbackSubmit(BaseModel):
    recommendation_id: str
    investigation_id: str
    outcome: str
    impact_description: str = ''
    executed_by: str = ''
    effectiveness_score: float = 0.0

@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackSubmit,
    request: Request,
    _ = Depends(require_permission(Permission.INCIDENT_INVESTIGATE))
):
    request_id = getattr(request.state, 'request_id', '')
    # Validate outcome against FeedbackOutcome enum
    try:
        outcome_enum = FeedbackOutcome(payload.outcome)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FeedbackOutcome")
        
    tracker = RecommendationFeedbackTracker()
    # Mock call tracker.submit()
    return make_response({"status": "submitted", "recommendation_id": payload.recommendation_id})

@router.get("/feedback/{investigation_id}")
async def list_feedback(
    investigation_id: str,
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    tracker = RecommendationFeedbackTracker()
    return make_response({"investigation_id": investigation_id, "items": []})

@router.get("/feedback/effectiveness")
async def get_effectiveness(
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    tracker = RecommendationFeedbackTracker()
    return make_response({"effectiveness_rate": 0.0})
