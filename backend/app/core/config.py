from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Ashu API"
    app_env: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    frontend_origins: str = "http://localhost:3000"

    clerk_secret_key: str | None = None
    clerk_jwt_key: str | None = None
    clerk_authorized_parties: str = "http://localhost:3000"
    clerk_webhook_signing_secret: str | None = None

    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    supabase_database_url: str | None = None

    integration_encryption_key: str | None = None

    ai_provider: Literal["gemini", "groq"] = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    digii_base_url: str = "https://bhawanipurglobal.digiicampus.com"
    digii_readonly_enabled: bool = False
    digii_auth_token: str | None = None
    digii_allowed_host: str = "bhawanipurglobal.digiicampus.com"
    digii_profile_path: str | None = None
    digii_courses_path: str | None = None
    digii_assignments_path: str | None = None
    digii_assignment_detail_path: str | None = None
    digii_resources_path: str | None = None
    digii_modules_path: str | None = None
    digii_sessions_path: str | None = None
    digii_feed_path: str | None = None
    digii_calendar_path: str | None = None
    digii_notifications_path: str | None = None
    digii_sync_interval_minutes: int = Field(default=15, ge=5, le=1440)

    max_upload_bytes: int = Field(default=20 * 1024 * 1024, ge=1024)
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_api_version: str = "v23.0"
    whatsapp_verify_token: str | None = None
    whatsapp_app_secret: str | None = None

    worker_poll_seconds: int = Field(default=3, ge=1, le=60)
    worker_visibility_timeout: int = Field(default=900, ge=10, le=3600)
    worker_batch_size: int = Field(default=5, ge=1, le=50)

    @field_validator("digii_base_url")
    @classmethod
    def https_for_digii(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Digiicampus base URL must use HTTPS")
        return value.rstrip("/")

    @property
    def frontend_origin_list(self) -> list[str]:
        return [x.strip() for x in self.frontend_origins.split(",") if x.strip()]

    @property
    def clerk_party_list(self) -> list[str]:
        return [x.strip() for x in self.clerk_authorized_parties.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
