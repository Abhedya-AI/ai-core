"""
domain/value_objects/bounding_box.py — Normalised bounding box value object.

Coordinates are expressed as fractions of the image dimensions ([0, 1])
so the same box applies to any camera resolution without conversion.

    (x_min, y_min) ─────────────┐
                   │             │
                   └─────────── (x_max, y_max)

Why Pydantic BaseModel + frozen=True?
──────────────────────────────────────
• Pydantic validates field constraints (ge/le) at construction time.
• ConfigDict(frozen=True) makes the object immutable — safe to pass
  between services and cache without defensive copying.
• FastAPI/Pydantic serialize it directly to JSON without extra adapters.

Why normalise?
──────────────
• Resolution-independent: same box for 720p, 1080p, 4K.
• Model-portable: YOLO outputs can be divided by (w, h) once in the
  mapper; no downstream code needs image dimensions.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BoundingBox(BaseModel):
    """
    Represents the location of a detected object in an image.
    Coordinates are normalized between 0.0 and 1.0.
    """

    model_config = ConfigDict(frozen=True)

    x_min: float = Field(..., ge=0.0, le=1.0, description="Left edge (normalised).")
    y_min: float = Field(..., ge=0.0, le=1.0, description="Top edge (normalised).")
    x_max: float = Field(..., ge=0.0, le=1.0, description="Right edge (normalised).")
    y_max: float = Field(..., ge=0.0, le=1.0, description="Bottom edge (normalised).")

    @model_validator(mode="after")
    def validate_coordinates(self) -> "BoundingBox":
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        return self

    # ── Derived geometry ──────────────────────────────────────────────────────

    @property
    def width(self) -> float:
        """Normalised width of the box."""
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """Normalised height of the box."""
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        """Normalised area (width × height)."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """(cx, cy) centre point of the box."""
        return (self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2

    # ── Pixel-space conversion ────────────────────────────────────────────────

    def to_pixel(
        self, image_width: int, image_height: int
    ) -> tuple[int, int, int, int]:
        """
        Convert normalised box to absolute pixel coordinates.

        Returns (x_min_px, y_min_px, x_max_px, y_max_px).
        """
        return (
            int(self.x_min * image_width),
            int(self.y_min * image_height),
            int(self.x_max * image_width),
            int(self.y_max * image_height),
        )

    # ── Serialisation helpers ─────────────────────────────────────────────────

    def as_dict(self) -> dict[str, float]:
        """Plain dict suitable for JSON serialisation."""
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "BoundingBox":
        return cls(
            x_min=data["x_min"],
            y_min=data["y_min"],
            x_max=data["x_max"],
            y_max=data["y_max"],
        )

    @classmethod
    def from_xyxy_pixels(
        cls,
        x_min: int,
        y_min: int,
        x_max: int,
        y_max: int,
        image_width: int,
        image_height: int,
    ) -> "BoundingBox":
        """
        Construct from absolute pixel coordinates by normalising them.

        Used inside the infrastructure mapper so the domain never
        sees raw pixel values.
        """
        return cls(
            x_min=x_min / image_width,
            y_min=y_min / image_height,
            x_max=x_max / image_width,
            y_max=y_max / image_height,
        )
