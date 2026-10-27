"""
Application configuration.

Loads settings from environment variables / .env file using pydantic-settings.
No secrets are hardcoded here - see .env.example for the expected keys.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "ECHO-ASSIST AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "insecure-dev-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./echo_assist.db"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Maps / Navigation
    MAPS_API_KEY: str = ""

    # AI Engine
    AI_DEVICE: str = "auto"
    AI_CONFIDENCE_THRESHOLD: float = 0.5
    AI_MOCK_MODE: bool = True

    # Emergency notification providers

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Resend Email
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""

    # Push notifications
    PUSH_NOTIFICATION_KEY: str = ""
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance, so the .env file is only parsed once."""
    return Settings()


settings = get_settings()
