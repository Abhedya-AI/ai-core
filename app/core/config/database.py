"""
database.py — Database connection settings.

Responsibility: connection parameters for PostgreSQL, Neo4j, Redis, and FAISS.
Exposes computed URL properties. No connection logic lives here.

Classes:
  DatabaseSettings  → PostgreSQL (accessed as settings.database)
  Neo4jSettings     → Neo4j graph database (accessed as settings.neo4j)
  RedisSettings     → Redis cache/queue (accessed as settings.redis)
  VectorStoreSettings → FAISS vector store (accessed as settings.vector_store)
"""

from pydantic import Field, computed_field

from app.core.config._base import _BaseConfig


class DatabaseSettings(_BaseConfig):
    """PostgreSQL relational database settings."""

    host: str = Field(
        default="localhost",
        alias="POSTGRES_HOST",
        description="PostgreSQL server hostname.",
    )
    port: int = Field(
        default=5432,
        alias="POSTGRES_PORT",
        description="PostgreSQL server port.",
    )
    name: str = Field(
        default="abhedya",
        alias="POSTGRES_DB",
        description="PostgreSQL database name.",
    )
    user: str = Field(
        default="postgres",
        alias="POSTGRES_USER",
        description="PostgreSQL username.",
    )
    password: str = Field(
        default="password",
        alias="POSTGRES_PASSWORD",
        description="PostgreSQL password.",
    )
    pool_size: int = Field(
        default=5,
        alias="POSTGRES_POOL_SIZE",
        description="SQLAlchemy connection pool size.",
    )
    max_overflow: int = Field(
        default=10,
        alias="POSTGRES_MAX_OVERFLOW",
        description="SQLAlchemy max pool overflow.",
    )
    connect_timeout: int = Field(
        default=3,
        alias="POSTGRES_CONNECT_TIMEOUT",
        description="Connection attempt timeout in seconds.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """Synchronous SQLAlchemy connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_url(self) -> str:
        """Async SQLAlchemy connection URL (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    # Backward-compat alias used in health checks
    @property
    def postgres_url(self) -> str:
        return self.url


class Neo4jSettings(_BaseConfig):
    """Neo4j graph database settings."""

    uri: str = Field(
        default="bolt://localhost:7687",
        alias="NEO4J_URI",
        description="Neo4j Bolt connection URI.",
    )
    username: str = Field(
        default="neo4j",
        alias="NEO4J_USERNAME",
        description="Neo4j username.",
    )
    password: str = Field(
        default="password",
        alias="NEO4J_PASSWORD",
        description="Neo4j password.",
    )
    max_connection_pool_size: int = Field(
        default=50,
        alias="NEO4J_MAX_POOL_SIZE",
        description="Maximum Neo4j driver connection pool size.",
    )
    connection_timeout: int = Field(
        default=5,
        alias="NEO4J_CONNECTION_TIMEOUT",
        description="Neo4j connection timeout in seconds.",
    )
    database: str = Field(
        default="neo4j",
        alias="NEO4J_DATABASE",
        description="Target Neo4j database name.",
    )


class RedisSettings(_BaseConfig):
    """Redis cache and session store settings."""

    host: str = Field(
        default="localhost",
        alias="REDIS_HOST",
        description="Redis server hostname.",
    )
    port: int = Field(
        default=6379,
        alias="REDIS_PORT",
        description="Redis server port.",
    )
    password: str | None = Field(
        default=None,
        alias="REDIS_PASSWORD",
        description="Redis password (None if no auth required).",
    )
    db: int = Field(
        default=0,
        alias="REDIS_DB",
        description="Redis logical database index.",
    )
    socket_timeout: int = Field(
        default=3,
        alias="REDIS_SOCKET_TIMEOUT",
        description="Redis socket read/write timeout in seconds.",
    )
    socket_connect_timeout: int = Field(
        default=3,
        alias="REDIS_CONNECT_TIMEOUT",
        description="Redis socket connect timeout in seconds.",
    )
    max_connections: int = Field(
        default=10,
        alias="REDIS_MAX_CONNECTIONS",
        description="Redis connection pool maximum size.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        """Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class VectorStoreSettings(_BaseConfig):
    """FAISS vector store settings."""

    provider: str = Field(
        default="faiss",
        alias="VECTOR_STORE_PROVIDER",
        description="Vector store backend: faiss | chroma.",
    )
    index_path: str = Field(
        default="faiss_index",
        alias="FAISS_INDEX_PATH",
        description="Local directory path for persisted FAISS index.",
    )
    dimension: int = Field(
        default=1024,
        alias="VECTOR_DIMENSION",
        description="Embedding dimension. BGE-M3 = 1024.",
    )
    nlist: int = Field(
        default=100,
        alias="FAISS_NLIST",
        description="Number of IVF clusters for approximate search.",
    )
