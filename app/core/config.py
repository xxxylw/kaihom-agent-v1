from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kaihom Agent API"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = "sqlite:///./kaihom_agent_local.db"
    upload_dir: str = "uploads"
    upload_max_file_size_bytes: int = 20 * 1024 * 1024
    upload_max_files_per_request: int = 10
    upload_max_request_size_bytes: int = 100 * 1024 * 1024
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: float = 30.0
    deepseek_max_retries: int = 1
    clarification_max_rounds: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="KAIHOM_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
