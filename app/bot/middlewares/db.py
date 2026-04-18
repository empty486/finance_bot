"""Database session middleware for aiogram — injects session into handler data."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    """Middleware that creates an async DB session per update and injects it.

    Handles:
    - Auto-commit on success (via session context manager)
    - Auto-rollback on exception
    - Proper session cleanup in all cases
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                return result
            except Exception as e:
                logger.error(f"Handler error, rolling back DB session: {e}")
                await session.rollback()
                raise
