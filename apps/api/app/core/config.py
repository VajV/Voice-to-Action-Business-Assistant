from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice-to-Action Business Assistant"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./voice_to_action.db"
    local_storage_dir: Path = Path("./storage")
    frontend_url: str = "http://localhost:3000"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    openai_api_key: str | None = None
    openai_transcription_model: str = "whisper-1"
    openai_analysis_model: str = "gpt-4o-mini"
    max_upload_mb: int = 200
    demo_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
