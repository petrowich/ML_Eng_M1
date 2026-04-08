from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: Optional[str] = None
    APP_PORT: Optional[int] = None
    DEBUG: Optional[bool] = None

    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    RABBITMQ_HOST: Optional[str] = None
    RABBITMQ_PORT: Optional[int] = None
    RABBITMQ_USER: Optional[str] = None
    RABBITMQ_PASSWORD: Optional[str] = None

    @property
    def database_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}://"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_psycopg(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()