import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "SIH 26008 Industrial Edge Gateway"
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 9000
    GATEWAY_ENV: str = "production"

    # Backend Ingest Endpoint
    BACKEND_URL: str = "http://localhost:8000"
    BACKEND_TIMEOUT_SECONDS: float = 3.0

    # Local SQLite persistent storage path
    BUFFER_DB_PATH: str = str(
        Path(__file__).resolve().parent.parent / "storage" / "buffer.db"
    )

    # Worker configuration
    POLL_INTERVAL_SECONDS: float = 1.0
    BATCH_SIZE: int = 20
    MAX_RETRY_BACKOFF_SECONDS: float = 5.0


settings = GatewaySettings()
