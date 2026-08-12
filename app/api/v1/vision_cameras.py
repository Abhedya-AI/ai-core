"""
app/api/v1/vision_cameras.py

Vision Intelligence - Cameras API.
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from pydantic import BaseModel
from typing import Any
from datetime import datetime

from app.core.logging import get_logger
from app.modules.vision.domain.entities.camera import Camera
from app.modules.vision.domain.entities.camera_group import CameraGroup
from app.modules.vision.domain.entities.camera_health import CameraHealth
from app.modules.vision.domain.enums.camera_status import CameraStatus
from app.modules.vision.infrastructure.repositories.in_memory_camera_repository import InMemoryCameraRepository
from app.modules.vision.application.camera.camera_service import CameraService
from app.modules.vision.application.camera.camera_service import CreateCameraRequest, UpdateCameraRequest

log = get_logger("api.v1.vision_cameras")

router = APIRouter(prefix="/cameras", tags=["Vision — Cameras"])

_camera_repo_instance = InMemoryCameraRepository()

def get_camera_repo() -> InMemoryCameraRepository:
    return _camera_repo_instance

def get_camera_service(repo=Depends(get_camera_repo)) -> CameraService:
    from app.modules.vision.infrastructure.vision_neo4j_repository import VisionNeo4jRepository
    from app.modules.vision.application.events.knowledge_graph_sync import VisionKnowledgeGraphSync
    kg = VisionKnowledgeGraphSync(VisionNeo4jRepository())
    return CameraService(camera_repo=repo, kg_sync=kg)

class CreateGroupRequest(BaseModel):
    name: str
    zone_id: str | None = None
    plant_id: str | None = None
    description: str | None = None

@router.post("", status_code=status.HTTP_201_CREATED, response_model=Camera)
async def create_camera(req: CreateCameraRequest, svc: CameraService = Depends(get_camera_service)):
    """Register a new camera."""
    return await svc.register_camera(req)

@router.get("", response_model=list[Camera])
async def list_cameras(
    zone_id: str | None = Query(None),
    group_id: str | None = Query(None),
    status: CameraStatus | None = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: InMemoryCameraRepository = Depends(get_camera_repo)
):
    """List cameras with filtering."""
    return await repo.list_cameras(zone_id, group_id, status, active_only, limit, offset)

# Static routes (/groups) defined BEFORE dynamic parameter routes (/{camera_id})
@router.post("/groups", status_code=status.HTTP_201_CREATED, response_model=CameraGroup)
async def create_group(req: CreateGroupRequest, repo: InMemoryCameraRepository = Depends(get_camera_repo)):
    """Create a camera group."""
    import uuid
    g = CameraGroup(
        id=str(uuid.uuid4()),
        name=req.name,
        zone_id=req.zone_id,
        plant_id=req.plant_id,
        description=req.description or "",
        camera_ids=[]
    )
    return await repo.save_group(g)

@router.get("/groups", response_model=list[CameraGroup])
async def list_groups(repo: InMemoryCameraRepository = Depends(get_camera_repo)):
    """List all camera groups."""
    return await repo.list_groups()

@router.get("/groups/{group_id}", response_model=CameraGroup)
async def get_group(group_id: str = Path(...), repo: InMemoryCameraRepository = Depends(get_camera_repo)):
    """Get group by ID."""
    g = await repo.get_group(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return g

@router.post("/groups/{group_id}/cameras/{camera_id}", status_code=status.HTTP_200_OK)
async def add_camera_to_group(
    group_id: str = Path(...), 
    camera_id: str = Path(...),
    repo: InMemoryCameraRepository = Depends(get_camera_repo)
):
    """Add camera to group."""
    g = await repo.get_group(group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if camera_id not in g.camera_ids:
        new_ids = list(g.camera_ids)
        new_ids.append(camera_id)
        g = g.model_copy(update={"camera_ids": new_ids})
        await repo.save_group(g)
    
    return {"status": "ok"}

# Dynamic parameter routes (/{camera_id})
@router.get("/{camera_id}", response_model=Camera)
async def get_camera(camera_id: str = Path(...), repo: InMemoryCameraRepository = Depends(get_camera_repo)):
    """Get single camera by ID."""
    cam = await repo.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam

@router.put("/{camera_id}", response_model=Camera)
async def update_camera(camera_id: str = Path(...), req: UpdateCameraRequest = ..., svc: CameraService = Depends(get_camera_service)):
    """Update camera configuration."""
    cam = await svc.update_camera(camera_id, req)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str = Path(...), svc: CameraService = Depends(get_camera_service)):
    """Deregister a camera."""
    success = await svc.deregister_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

@router.get("/{camera_id}/health", response_model=CameraHealth)
async def get_camera_health(camera_id: str = Path(...), repo: InMemoryCameraRepository = Depends(get_camera_repo)):
    """Get camera health metrics."""
    h = await repo.get_health(camera_id)
    if not h:
        cam = await repo.get_camera(camera_id)
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found")
        return CameraHealth(camera_id=camera_id, status=cam.health_status)
    return h

@router.post("/{camera_id}/heartbeat", status_code=status.HTTP_200_OK)
async def heartbeat_camera(camera_id: str = Path(...), svc: CameraService = Depends(get_camera_service)):
    """Update camera heartbeat."""
    success = await svc.handle_heartbeat(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"status": "ok"}

@router.post("/{camera_id}/snapshot")
async def snapshot_camera(camera_id: str = Path(...)):
    """Trigger a manual snapshot."""
    return {"camera_id": camera_id, "message": "Snapshot triggered", "timestamp": datetime.now().isoformat()}
