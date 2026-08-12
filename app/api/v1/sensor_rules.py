"""
app/api/v1/sensor_rules.py — Sensor Rule Engine API.

Tag: Rules
Prefix: /rules
"""
from __future__ import annotations
import uuid
from typing import Optional, List
from fastapi import APIRouter, Query, Path, Body
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, make_response
from app.api.exceptions import NotFoundError, ValidationError
from app.modules.sensor.application.rule_engine import SensorRuleEngine
from app.modules.sensor.domain.rule_models import (
    SensorRule, RuleCondition, RuleAction, RulePriority, RuleScope, RuleConditionOperator, RuleActionType
)
from app.core.logging import get_logger

log = get_logger("api.v1.sensor_rules")

router = APIRouter(prefix="/rules", tags=["Rules"])

_rule_engine = SensorRuleEngine()

class CreateRuleRequest(BaseModel):
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    scope: RuleScope = Field(RuleScope.SENSOR, description="Scope of the rule")
    sensor_id: Optional[str] = Field(None, description="Target sensor ID")
    conditions: List[RuleCondition] = Field(default_factory=list, description="List of conditions")
    actions: List[RuleAction] = Field(default_factory=list, description="List of actions")
    priority: RulePriority = Field(RulePriority.P3, description="Rule priority")
    enabled: bool = Field(True, description="Whether rule is enabled")

@router.get("", response_model=StandardResponse, summary="List Rules", description="List all configured rules.")
async def list_rules(
    scope: Optional[RuleScope] = Query(None, description="Filter by scope"),
    priority: Optional[RulePriority] = Query(None, description="Filter by priority"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled state"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Max results per page")
):
    try:
        rules = _rule_engine.get_all_rules()
        
        if scope:
            rules = [r for r in rules if r.scope == scope]
        if priority:
            rules = [r for r in rules if r.priority == priority]
        if enabled is not None:
            rules = [r for r in rules if r.enabled == enabled]
            
        start = (page - 1) * limit
        paginated = rules[start:start+limit]
        
        return make_response(
            data=[r.model_dump() if hasattr(r, 'model_dump') else r for r in paginated],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to list rules: {str(e)}")
        raise ValidationError(message=f"Failed to list rules: {str(e)}")

@router.get("/stats/overall", response_model=StandardResponse, summary="Rule Stats", description="Get rule engine statistics.")
async def get_rule_stats():
    try:
        stats = _rule_engine.get_stats()
        return make_response(
            data=stats,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get rule stats: {str(e)}")
        raise ValidationError(message=f"Failed to get rule stats: {str(e)}")

@router.get("/triggers/history", response_model=StandardResponse, summary="Rule Trigger History", description="Get history of triggered rules.")
async def get_trigger_history(
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    limit: int = Query(50, ge=1, le=1000, description="Max results"),
    page: int = Query(1, ge=1, description="Page number")
):
    try:
        history = _rule_engine.get_trigger_history(rule_id=rule_id, limit=limit, offset=(page-1)*limit)
        
        return make_response(
            data=[h.model_dump() if hasattr(h, 'model_dump') else h for h in history],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to get trigger history: {str(e)}")
        raise ValidationError(message=f"Failed to get trigger history: {str(e)}")

@router.get("/{rule_id}", response_model=StandardResponse, summary="Get Rule", description="Get a specific rule by ID.")
async def get_rule(rule_id: str = Path(..., description="Rule ID")):
    try:
        rule = _rule_engine.get_rule(rule_id)
        if not rule:
            raise NotFoundError(message=f"Rule {rule_id} not found")
            
        return make_response(
            data=rule.model_dump() if hasattr(rule, 'model_dump') else rule,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except NotFoundError:
        raise
    except Exception as e:
        log.error(f"Failed to get rule {rule_id}: {str(e)}")
        raise ValidationError(message=f"Failed to get rule: {str(e)}")

@router.post("", response_model=StandardResponse, summary="Create Rule", description="Create a new sensor rule.")
async def create_rule(request: CreateRuleRequest):
    try:
        rule = SensorRule(
            rule_id=str(uuid.uuid4()),
            name=request.name,
            description=request.description or "",
            scope=request.scope,
            sensor_id=request.sensor_id,
            conditions=request.conditions,
            actions=request.actions,
            priority=request.priority,
            enabled=request.enabled
        )
        created = _rule_engine.add_rule(rule)
        
        return make_response(
            data=created.model_dump() if hasattr(created, 'model_dump') else created,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Failed to create rule: {str(e)}")
        raise ValidationError(message=f"Failed to create rule: {str(e)}")

@router.delete("/{rule_id}", response_model=StandardResponse, summary="Delete Rule", description="Delete a sensor rule.")
async def delete_rule(rule_id: str = Path(..., description="Rule ID")):
    try:
        success = _rule_engine.delete_rule(rule_id)
        if not success:
            raise NotFoundError(message=f"Rule {rule_id} not found")
            
        return make_response(
            data={"deleted": True, "rule_id": rule_id},
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except NotFoundError:
        raise
    except Exception as e:
        log.error(f"Failed to delete rule {rule_id}: {str(e)}")
        raise ValidationError(message=f"Failed to delete rule: {str(e)}")

@router.patch("/{rule_id}/enable", response_model=StandardResponse, summary="Enable Rule", description="Enable a sensor rule.")
async def enable_rule(rule_id: str = Path(..., description="Rule ID")):
    try:
        updated = _rule_engine.enable_rule(rule_id)
        if not updated:
            raise NotFoundError(message=f"Rule {rule_id} not found")
            
        return make_response(
            data=updated.model_dump() if hasattr(updated, 'model_dump') else updated,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except NotFoundError:
        raise
    except Exception as e:
        log.error(f"Failed to enable rule {rule_id}: {str(e)}")
        raise ValidationError(message=f"Failed to enable rule: {str(e)}")

@router.patch("/{rule_id}/disable", response_model=StandardResponse, summary="Disable Rule", description="Disable a sensor rule.")
async def disable_rule(rule_id: str = Path(..., description="Rule ID")):
    try:
        updated = _rule_engine.disable_rule(rule_id)
        if not updated:
            raise NotFoundError(message=f"Rule {rule_id} not found")
            
        return make_response(
            data=updated.model_dump() if hasattr(updated, 'model_dump') else updated,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except NotFoundError:
        raise
    except Exception as e:
        log.error(f"Failed to disable rule {rule_id}: {str(e)}")
        raise ValidationError(message=f"Failed to disable rule: {str(e)}")
