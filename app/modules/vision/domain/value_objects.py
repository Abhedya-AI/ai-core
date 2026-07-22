"""
domain/value_objects.py — Immutable value objects for the Vision domain.

Value objects carry data and domain behaviour but have no identity of
their own.  They are compared by value, not by reference.

Rules
─────
• frozen=True — never mutated after construction.
• All validation lives here, not in application or infrastructure layers.
• No ORM, no FastAPI, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── BoundingBox ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BoundingBox:
    """
    Normalised axis-aligned bounding box in image space.

    Coordinates are expressed as fractions of the image dimensions
    (range [0.0, 1.0]), so the same box can be applied to any
    resolution without conversion.

        (x1, y1) ─────────────┐
                │              │
                └──────────── (x2, y2)

    Attributes
    ──────────
    x1, y1  Upper-left corner (top, left in image coordinates).
    x2, y2  Lower-right corner (bottom, right).
    """

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        for name, value in [("x1", self.x1), ("y1", self.y1),
                             ("x2", self.x2), ("y2", self.y2)]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"BoundingBox.{name} must be in [0, 1]; got {value}"
                )
        if self.x1 >= self.x2:
            raise ValueError(
                f"BoundingBox.x1 ({self.x1}) must be less than x2 ({self.x2})"
            )
        if self.y1 >= self.y2:
            raise ValueError(
                f"BoundingBox.y1 ({self.y1}) must be less than y2 ({self.y2})"
            )

    # ── Derived geometry ──────────────────────────────────────────────────────

    @property
    def width(self) -> float:
        """Normalised width of the box."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Normalised height of the box."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Normalised area (width × height)."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """(cx, cy) centre point of the box."""
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    # ── Pixel-space conversion ────────────────────────────────────────────────

    def to_pixel(
        self, image_width: int, image_height: int
    ) -> tuple[int, int, int, int]:
        """
        Convert normalised box to absolute pixel coordinates.

        Returns (x1_px, y1_px, x2_px, y2_px).
        """
        return (
            int(self.x1 * image_width),
            int(self.y1 * image_height),
            int(self.x2 * image_width),
            int(self.y2 * image_height),
        )

    # ── Serialisation ─────────────────────────────────────────────────────────

    def as_dict(self) -> dict[str, float]:
        """Plain dict suitable for JSON serialisation."""
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "BoundingBox":
        return cls(x1=data["x1"], y1=data["y1"], x2=data["x2"], y2=data["y2"])

    @classmethod
    def from_xyxy_pixels(
        cls,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        image_width: int,
        image_height: int,
    ) -> "BoundingBox":
        """
        Construct from absolute pixel coordinates by normalising them.

        Useful inside the infrastructure mapper so the domain never
        sees raw pixel values.
        """
        return cls(
            x1=x1 / image_width,
            y1=y1 / image_height,
            x2=x2 / image_width,
            y2=y2 / image_height,
        )


# ── RiskScore ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RiskScore:
    """
    Aggregated risk score for a single frame analysis.

    Attributes
    ──────────
    value       Float in [0.0, 1.0].  Higher → more dangerous.
    level       Discretised RiskLevel derived from the value.
    contributing_hazards
                Tuple of (HazardType, weight) pairs that drove this score.
                Useful for explanation / audit.
    """

    from app.modules.vision.domain.enums import RiskLevel, HazardType  # local import to avoid circular

    value: float
    level: "RiskLevel"
    contributing_hazards: tuple[tuple["HazardType", float], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"RiskScore.value must be in [0, 1]; got {self.value}"
            )

    @property
    def is_actionable(self) -> bool:
        """True when the score demands operator intervention (HIGH or CRITICAL)."""
        from app.modules.vision.domain.enums import RiskLevel
        return self.level >= RiskLevel.HIGH

    def as_dict(self) -> dict:
        return {
            "value": self.value,
            "level": self.level.value,
            "contributing_hazards": [
                {"hazard": h.value, "weight": w}
                for h, w in self.contributing_hazards
            ],
        }
