from fastapi import APIRouter, Depends, Request, Query, HTTPException
from app.api.responses import StandardResponse, make_response
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission
from app.core.logging import get_logger
from app.modules.root_cause.context.investigation_context_builder import InvestigationContextBuilder

log = get_logger("root_cause.api.context")
router = APIRouter()

@router.get("/context/{investigation_id}")
async def get_context(
    investigation_id: str,
    request: Request,
    _ = Depends(require_permission(Permission.GRAPH_READ))
):
    request_id = getattr(request.state, 'request_id', '')
    builder = InvestigationContextBuilder()
    # Mocking Investigation as an empty context since InvestigationService is in-memory only
    return make_response({"investigation_id": investigation_id, "context": {}})
