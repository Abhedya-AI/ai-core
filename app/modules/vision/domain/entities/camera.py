from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Camera(BaseModel):
    """
    Camera registered in the Vision System.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID

    name: str = Field(..., min_length=1, max_length=100)

    location: str = Field(..., min_length=1)

    is_active: bool = True

    created_at: datetime
