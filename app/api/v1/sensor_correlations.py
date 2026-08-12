"""
app/api/v1/sensor_correlations.py — Sensor Correlation API.

Tag: Correlations
Prefix: /correlations
"""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Query, Path, Body
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.application.correlation_service import SensorCorrelationService
from app.modules.sensor.domain.correlation_models import CorrelationPair, CorrelationScope
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_correlations")

router = APIRouter(prefix="/correlations", tags=["Correlations"])

_correlation_service = SensorCorrelationService()

class CorrelationPairRequest(BaseModel):
    sensor_id_a: str = Field(..., description="First sensor ID")
    sensor_id_b: str = Field(..., description="Second sensor ID")
    scope: CorrelationScope = Field(CorrelationScope.GLOBAL, description="Scope of the correlation")
    expected_correlation: Optional[float] = Field(0.75, description="Expected correlation coefficient (-1.0 to 1.0)")

@router.get("", response_model=StandardResponse, summary="List Correlation Pairs", description="List all registered correlation pairs.")
async def list_correlation_pairs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Max results")
):
    try:
        pairs = _correlation_service.get_all_pairs()
        start = (page - 1) * limit
        paginated = pairs[start:start+limit]
        
        return make_response(
            data=[p.model_dump() if hasattr(p, 'model_dump') else p for p in paginated],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to list correlation pairs: {str(e)}")
        raise ValidationError(message=f"Failed to list pairs: {str(e)}")

@router.get("/results", response_model=StandardResponse, summary="Get Correlation Results", description="Get all latest correlation computation results.")
async def get_correlation_results():
    try:
        results = _correlation_service.get_latest_results()
        return make_response(
            data=[r.model_dump() if hasattr(r, 'model_dump') else r for r in results],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get correlation results: {str(e)}")
        raise ValidationError(message=f"Failed to get results: {str(e)}")

@router.get("/alerts", response_model=StandardResponse, summary="Get Correlation Alerts", description="Get recent correlation break alerts.")
async def get_correlation_alerts(limit: int = Query(50, ge=1, le=1000)):
    try:
        alerts = _correlation_service.get_alerts(limit=limit)
        return make_response(
            data=[a.model_dump() if hasattr(a, 'model_dump') else a for a in alerts],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get correlation alerts: {str(e)}")
        raise ValidationError(message=f"Failed to get alerts: {str(e)}")

@router.post("/pairs", response_model=StandardResponse, summary="Register Pair", description="Register a new sensor correlation pair.")
async def register_pair(request: CorrelationPairRequest):
    try:
        pair = CorrelationPair(
            sensor_id_a=request.sensor_id_a,
            sensor_id_b=request.sensor_id_b,
            scope=request.scope,
            expected_correlation=request.expected_correlation
        )
        _correlation_service.register_pair(pair)
        return make_response(
            data=pair.model_dump() if hasattr(pair, 'model_dump') else pair,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to register correlation pair: {str(e)}")
        raise ValidationError(message=f"Failed to register pair: {str(e)}")

@router.post("/evaluate", response_model=StandardResponse, summary="Evaluate Correlations", description="Trigger cross-sensor correlation evaluation.")
async def evaluate_correlations():
    try:
        alerts = _correlation_service.evaluate_correlations()
        return make_response(
            data=[a.model_dump() if hasattr(a, 'model_dump') else a for a in alerts],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to evaluate correlations: {str(e)}")
        raise ValidationError(message=f"Evaluation failed: {str(e)}")
