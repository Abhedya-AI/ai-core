"""
ABHEDYA Configuration Package — public API.

The only import rule for the entire project:

    from app.core.config import settings

    settings.app.name
    settings.app.is_production
    settings.database.url
    settings.database.postgres_url
    settings.neo4j.uri
    settings.redis.url
    settings.llm.provider
    settings.llm.active_api_key
    settings.llm.active_model
    settings.kafka.enabled
    settings.logging.level
    settings.security.secret_key
    settings.vector_store.index_path

Nobody should ever use:
    os.getenv(...)
    dotenv.load_dotenv(...)
    open(".env")
"""

from app.core.config.settings import Settings, settings

__all__ = ["settings", "Settings"]
