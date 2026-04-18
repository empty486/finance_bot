"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration from .env file."""

    # Telegram
    bot_token: str = Field(default="", description="Telegram bot token from @BotFather")

    # Gemini AI
    gemini_api_key: str = Field(default="", description="Google Gemini API key")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/finance_db",
        description="PostgreSQL connection string (asyncpg driver)",
    )

    # FastAPI
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8000, description="API bind port")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Convenience alias — instantiated on first access
settings = get_settings()
