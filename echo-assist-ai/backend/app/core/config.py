"""
Application configuration.

Loads settings from environment variables / .env file using pydantic-settings.
No secrets are hardcoded here - see .env.example for the expected keys.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
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
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Database
    DATABASE_URL: str = "postgresql+psycopg://echo_assist:echo_assist@localhost:5432/echo_assist"
    DATABASE_CONNECT_TIMEOUT_SECONDS: int = 5

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value: object) -> object:
        """Accept legacy deployment labels while keeping DEBUG a real boolean."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"development", "dev"}:
                return True
        return value

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    ALLOWED_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

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
    FRONTEND_BASE_URL: str = "http://localhost:8000"

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
