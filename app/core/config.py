from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kaihom Agent API"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = "sqlite:///./kaihom_agent_local.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="KAIHOM_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
