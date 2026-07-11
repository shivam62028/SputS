"""
Application configuration via environment variables.

Uses pydantic-settings to load and validate all config from env vars,
making it easy to switch between local (docker-compose) and production.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the SputS backend."""

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://sputs:sputs_secret@localhost:5432/sputs_db"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Distributed Lock ──────────────────────────────────────
    LOCK_TTL_SECONDS: int = 300  # 5 minutes

    # ── App ───────────────────────────────────────────────────
    APP_NAME: str = "SputS"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance — import this everywhere
settings = Settings()
