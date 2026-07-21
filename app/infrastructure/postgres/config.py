"""postgres/config.py — PostgreSQL pool and connection configuration."""

from app.core.config import settings

_db = settings.database


class PostgresConfig:
    """PostgreSQL-specific configuration constants."""

    # ── Connection ─────────────────────────────────────────────────────────────
    HOST: str = _db.host
    PORT: int = _db.port
    DATABASE: str = _db.database
    USERNAME: str = _db.username
    PASSWORD: str = _db.password

    # ── Async URL (asyncpg driver) ─────────────────────────────────────────────
    ASYNC_URL: str = (
        f"postgresql+asyncpg://{_db.username}:{_db.password}"
        f"@{_db.host}:{_db.port}/{_db.database}"
    )

    # ── Pool ───────────────────────────────────────────────────────────────────
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30          # seconds to wait for a connection
    POOL_RECYCLE: int = 1800        # recycle connections every 30 minutes
    POOL_PRE_PING: bool = True      # validate connections before use

    # ── Connection ─────────────────────────────────────────────────────────────
    CONNECT_TIMEOUT: int = 10       # seconds before giving up on connect
    COMMAND_TIMEOUT: int = 30       # seconds before cancelling a query

    # ── Echo ───────────────────────────────────────────────────────────────────
    ECHO_SQL: bool = settings.app.debug  # log SQL only in debug mode
