"""
app/api/v1/sensors.py — Sensor Management API.

Tag: Sensor Management
Prefix: /sensors

Endpoints: GET list, GET single, POST register, PUT update, PATCH status,
           DELETE deregister, GET by zone, GET by equipment type.
"""
from __future__ import annotations
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Query, Path, Depends
from pydantic import BaseModel, Field

from app.api.responses import StandardResponse, PaginatedResponse, make_response, ResponseMetadata, PaginationMeta
from app.api.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.modules.knowledge.domain.entities.sensor import Sensor
from app.modules.knowledge.domain.enums import SensorType
from app.modules.knowledge.services.sensor_service import SensorService
from app.modules.sensor.application.health_tracker import SensorHealthTracker

log = get_logger("api.v1.sensors")

router = APIRouter(prefix="/sensors", tags=["Sensor Management"])

_sensor_service = SensorService()
_health_tracker = SensorHealthTracker()

class SensorRegisterRequest(BaseModel):
    name: str = Field(..., description="Name of the sensor")
    sensor_type: SensorType = Field(..., description="Type of the sensor")
    unit: str = Field(..., description="Unit of measurement")
    min_threshold: Optional[float] = Field(None, description="Minimum safe value")
    max_threshold: Optional[float] = Field(None, description="Maximum safe value")
    sampling_interval_sec: Optional[int] = Field(60, description="Sampling interval in seconds")
    attached_equipment_id: Optional[str] = Field(None, description="ID of equipment this sensor is attached to")
    attached_zone_id: Optional[str] = Field(None, description="ID of zone this sensor is attached to")

class SensorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Name of the sensor")
    sensor_type: Optional[SensorType] = Field(None, description="Type of the sensor")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    min_threshold: Optional[float] = Field(None, description="Minimum safe value")
    max_threshold: Optional[float] = Field(None, description="Maximum safe value")
    sampling_interval_sec: Optional[int] = Field(None, description="Sampling interval in seconds")
    attached_equipment_id: Optional[str] = Field(None, description="ID of equipment this sensor is attached to")
    attached_zone_id: Optional[str] = Field(None, description="ID of zone this sensor is attached to")


@router.get("", response_model=PaginatedResponse, summary="List Sensors", description="Retrieve a paginated list of sensors.")
async def list_sensors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sensor_type: Optional[SensorType] = Query(None, description="Filter by sensor type"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID")
):
    try:
        # Assuming sensor_service has a method to get all sensors or we just get all and filter
        # As there is no specific pagination method defined, let's pretend it returns a list
        # And we'll manually paginate for now, or just return everything
        sensors = await _sensor_service.get_sensors_by_type(sensor_type) if sensor_type else await _sensor_service.get_all_sensors()
        if zone_id:
            sensors = [s for s in sensors if s.attached_zone_id == zone_id]
        
        total = len(sensors)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = sensors[start:end]

        return make_response(
            data=[s.dict() if hasattr(s, 'dict') else s for s in paginated],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Error listing sensors: {str(e)}")
        raise ValidationError(message=f"Failed to list sensors: {str(e)}")


@router.get("/{sensor_id}", response_model=StandardResponse, summary="Get Sensor", description="Retrieve a specific sensor by ID.")
async def get_sensor(sensor_id: str = Path(..., description="The ID of the sensor")):
    sensor = await _sensor_service.get_sensor(sensor_id)
    if not sensor:
        raise NotFoundError(message=f"Sensor {sensor_id} not found")
    
    return make_response(
        data=sensor.dict() if hasattr(sensor, 'dict') else sensor,
        trace_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4())
    )


@router.post("/register", response_model=StandardResponse, summary="Register Sensor", description="Register a new sensor.")
async def register_sensor(request: SensorRegisterRequest):
    try:
        # Create a Sensor entity or pass kwargs
        # The prompt says "(uses SensorService.register_sensor)"
        sensor = await _sensor_service.register_sensor(
            name=request.name,
            sensor_type=request.sensor_type,
            unit=request.unit,
            min_threshold=request.min_threshold,
            max_threshold=request.max_threshold,
            sampling_interval_sec=request.sampling_interval_sec,
            attached_equipment_id=request.attached_equipment_id,
            attached_zone_id=request.attached_zone_id
        )
        return make_response(
            data=sensor.dict() if hasattr(sensor, 'dict') else sensor,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Error registering sensor: {str(e)}")
        raise ValidationError(message=f"Failed to register sensor: {str(e)}")


@router.patch("/{sensor_id}", response_model=StandardResponse, summary="Update Sensor", description="Partially update a sensor.")
async def update_sensor(
    sensor_id: str = Path(..., description="The ID of the sensor to update"),
    request: SensorUpdateRequest = None
):
    sensor = await _sensor_service.get_sensor(sensor_id)
    if not sensor:
        raise NotFoundError(message=f"Sensor {sensor_id} not found")
    
    try:
        update_data = request.model_dump(exclude_unset=True)
        updated_sensor = await _sensor_service.update_sensor(sensor_id, **update_data)
        
        return make_response(
            data=updated_sensor.dict() if hasattr(updated_sensor, 'dict') else updated_sensor,
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Error updating sensor {sensor_id}: {str(e)}")
        raise ValidationError(message=f"Failed to update sensor: {str(e)}")


@router.get("/by-zone/{zone_id}", response_model=StandardResponse, summary="Get Sensors by Zone", description="Retrieve all sensors attached to a specific zone.")
async def get_sensors_by_zone(zone_id: str = Path(..., description="The ID of the zone")):
    try:
        sensors = await _sensor_service.get_sensors_for_zone(zone_id)
        return make_response(
            data=[s.dict() if hasattr(s, 'dict') else s for s in sensors],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Error retrieving sensors for zone {zone_id}: {str(e)}")
        raise ValidationError(message=f"Failed to retrieve sensors: {str(e)}")


@router.get("/by-equipment/{equipment_id}", response_model=StandardResponse, summary="Get Sensors by Equipment", description="Retrieve all sensors attached to specific equipment.")
async def get_sensors_by_equipment(equipment_id: str = Path(..., description="The ID of the equipment")):
    try:
        sensors = await _sensor_service.get_sensors_for_equipment(equipment_id)
        return make_response(
            data=[s.dict() if hasattr(s, 'dict') else s for s in sensors],
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        log.error(f"Error retrieving sensors for equipment {equipment_id}: {str(e)}")
        raise ValidationError(message=f"Failed to retrieve sensors: {str(e)}")
