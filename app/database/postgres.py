"""
PostgreSQL connection manager.

Exposes:
    engine          — SQLAlchemy engine (sync)
    SessionLocal    — session factory
    Base            — declarative base for models
    get_db()        — FastAPI dependency
    check_health()  — returns True if Postgres is reachable
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config.settings import database
from app.core.logger import get_logger

log = get_logger("PostgreSQL")

engine = create_engine(
    database.postgres_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_health() -> bool:
    """Return True if PostgreSQL is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        log.error(f"Health check failed: {exc}")
        return False
