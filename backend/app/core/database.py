import logging
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_engine() -> AsyncEngine:
    """Create the shared async database engine from environment configuration."""
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


async def check_database_connection() -> bool:
    """Return whether PostgreSQL responds to a minimal readiness query."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.warning(
            "Database readiness check failed",
            extra={"event": "database_readiness_failed", "error_type": type(error).__name__},
        )
        return False
    return True

