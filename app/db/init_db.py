"""Database initialization — creates all tables on startup."""

import logging

from app.db.base import Base
from app.db.engine import engine

# Import all models so they register with Base.metadata
from app.models.transaction import Transaction  # noqa: F401
from app.models.category import Category  # noqa: F401

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all database tables if they don't exist."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")
