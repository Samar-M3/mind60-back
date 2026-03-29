"""
Centralized configuration using pydantic-settings.
Keeps environment-driven settings in one place so the rest of the codebase
can rely on typed, validated values.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env file."""

    # Firebase
    firebase_credentials_path: Optional[str] = None

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # AI keys (optional)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Admin access
    admin_uids: List[str] = []

    # Misc
    environment: str = "development"
    frontend_url: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()

