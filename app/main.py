"""Main entry point — runs Telegram bot with polling (production-ready)."""

import asyncio
import logging
import sys

from app.config import settings

# Configure logging BEFORE any imports that use logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

# Suppress noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    """Initialize DB and start bot polling."""
    logger.info("=" * 50)
    logger.info("🚀 Finance Bot v1.0 starting...")
    logger.info("=" * 50)

    # Validate required env vars
    if not settings.bot_token:
        logger.error("❌ BOT_TOKEN is not set in .env!")
        sys.exit(1)
    if not settings.gemini_api_key:
        logger.error("❌ GEMINI_API_KEY is not set in .env!")
        sys.exit(1)

    logger.info(f"📦 Database: {settings.database_url.split('@')[-1]}")

    # Import after config validation
    from app.bot.bot import setup_bot
    from app.db.init_db import init_db

    # Create tables
    try:
        await init_db()
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Start bot with retries for poor connectivity
    bot, dp = setup_bot()
    
    bot_info = None
    for attempt in range(1, 6):
        try:
            bot_info = await bot.get_me()
            break
        except Exception as e:
            logger.warning(f"⚠️ Bot startup attempt {attempt} failed: {e}")
            if attempt == 5:
                logger.error("💥 Failed to connect to Telegram after 5 attempts.")
                sys.exit(1)
            await asyncio.sleep(2 * attempt)

    logger.info(f"🤖 Bot: @{bot_info.username} (id={bot_info.id})")
    logger.info("✅ Bot is running (polling mode)...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,  # Don't process old messages on restart
        )
    finally:
        await bot.session.close()
        logger.info("🔌 Bot session closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Finance Bot stopped.")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
