from functools import lru_cache
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import field_validator
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    curse_forge_api: str = Field(default="", alias="CURSE_FORGE_API")
    curse_forge_api_file: Optional[Path] = Field(default=None, alias="CURSE_FORGE_API_FILE")

    app_base_path: Path = Field(default=Path("."), alias="APP_BASE_PATH")
    sync_interval: int = Field(default=0, alias="SYNC_INTERVAL", ge=0)

    max_mod_file_size_mb: int = Field(default=1024, alias="MAX_MOD_FILE_SIZE_MB", gt=0)
    download_timeout_seconds: float = Field(default=60.0, alias="DOWNLOAD_TIMEOUT_SECONDS", gt=0)
    connect_timeout_seconds: float = Field(default=10.0, alias="CONNECT_TIMEOUT_SECONDS", gt=0)
    
    timezone: str = Field(default="UTC", alias="APP_TIMEZONE")

    @property
    def max_mod_file_size_bytes(self) -> int:
        return self.max_mod_file_size_mb * 1024 * 1024

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        ZoneInfo(value)  # raises if invalid
        return value

    @model_validator(mode="after")
    def resolve_api_key(self) -> "Settings":
        if not self.curse_forge_api and self.curse_forge_api_file:
            self.curse_forge_api = self.curse_forge_api_file.read_text(encoding="utf-8").strip()

        if not self.curse_forge_api:
            raise ValueError("CURSE_FORGE_API (or CURSE_FORGE_API_FILE) is required.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()