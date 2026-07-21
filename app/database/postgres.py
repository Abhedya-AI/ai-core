"""
postgres.py — PostgreSQL connection manager.

Public interface:
    engine          — SQLAlchemy sync engine
    SessionLocal    — session factory
    Base            — declarative base for ORM models
    get_db()        — FastAPI dependency (yields a session)
    check_health()  — returns True if Postgres is reachable
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger("PostgreSQL")

engine = create_engine(
    settings.database.url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_health() -> bool:
    """Return True if PostgreSQL is reachable via a lightweight query."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        log.error(f"Health check failed: {exc}")
        return False
