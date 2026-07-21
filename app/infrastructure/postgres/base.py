"""postgres/base.py — SQLAlchemy DeclarativeBase. Nothing else lives here."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Usage:
        from app.infrastructure.postgres.base import Base

        class SensorReading(Base):
            __tablename__ = "sensor_readings"
            id: Mapped[int] = mapped_column(primary_key=True)
    """
