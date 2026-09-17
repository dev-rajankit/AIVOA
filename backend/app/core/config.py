"""
AIVOA — Application Settings

Centralized configuration loaded from environment variables / .env file.
Uses pydantic-settings for type-safe, validated configuration with
automatic .env file loading.

Every config value that could change between environments (dev / staging /
production) lives here, never hardcoded in application code. This is also
what makes the Groq model-deprecation issue (§1 of the architecture doc)
a five-second env-var fix instead of a code change.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/aivoa"

    # --- LLM (Groq) — not used in Chunk 2, but validated at startup ---
    GROQ_API_KEY: str = ""
    EXTRACTION_MODEL: str = "openai/gpt-oss-20b"
    REASONING_MODEL: str = "openai/gpt-oss-120b"

    # --- Application ---
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # --- Duplicate Detection ---
    DUPLICATE_THRESHOLD: float = 0.85
    POSSIBLE_DUPLICATE_THRESHOLD: float = 0.70
    TOP_K_DUPLICATES: int = 5


    # --- Risk Assessment ---
    RPN_CRITICAL_THRESHOLD: int = 500
    RPN_HIGH_THRESHOLD: int = 200
    RPN_MEDIUM_THRESHOLD: int = 100

settings = Settings()
