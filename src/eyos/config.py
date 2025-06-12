from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    api_title: str = "NewStore to Hail Integration"
    api_description: str = "Service for integrating NewStore order events with eyos Hail API"
    api_version: str = "0.1.0"

    # NewStore webhook settings
    newstore_webhook_secret: str = Field(default="mock_webhook_secret")
    newstore_supported_events: List[str] = ["order.completed"]

    # Hail API settings
    hail_api_base_url: str = Field(default="mock")
    hail_api_key: str = Field(default="mock_api_key")
    hail_api_max_retries: int = 3
    hail_api_retry_delay: float = 1.0  # Base delay in seconds

    # Queue settings (for future implementation)
    queue_enabled: bool = False
    queue_url: Optional[str] = None

    # Logging settings
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EYOS_",
    )


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
