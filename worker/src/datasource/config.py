import logging
from typing import Optional
from functools import lru_cache

from pika import ConnectionParameters, PlainCredentials
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: Optional[str] = None
    LOG_LEVEL: Optional[str] = 'INFO'
    POOL_TYPE: Optional[str] = None

    RABBITMQ_HOST: Optional[str] = None
    RABBITMQ_PORT: Optional[int] = None
    RABBITMQ_USER: Optional[str] = None
    RABBITMQ_PASSWORD: Optional[str] = None
    RABBITMQ_HEARTBEAT: Optional[int] = None
    RABBITMQ_BLOCKED_CONNECTION_TIMEOUT: Optional[int] = None

    QUEUE_ML_TASKS: Optional[str] = None

    @property
    def pika_connection_parameters(self) -> ConnectionParameters:
        rabbitmq_host = self.RABBITMQ_HOST or 'rabbitmq'
        rabbitmq_port = self.RABBITMQ_PORT or 5672
        rabbitmq_user = self.RABBITMQ_USER or 'guest'
        rabbitmq_password = self.RABBITMQ_PASSWORD or 'guest'
        heartbeat=self.RABBITMQ_HEARTBEAT
        blocked_connection_timeout=self.RABBITMQ_BLOCKED_CONNECTION_TIMEOUT
        credentials = PlainCredentials(username=rabbitmq_user, password=rabbitmq_password)

        return ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials,
            heartbeat=heartbeat,
            blocked_connection_timeout=blocked_connection_timeout)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )

    @property
    def broker(self) -> str:
        return f'amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//'

    @property
    def input_queue(self) -> str:
        return self.QUEUE_ML_TASKS or 'ML_Tasks'

    @model_validator(mode='after')
    def check_required_fields(self) -> 'Settings':
        # Проверяем, что ключевые поля не None
        required_fields = {
            'APP_NAME': self.APP_NAME,
            'POOL_TYPE': self.POOL_TYPE,

            'RABBITMQ_HOST': self.RABBITMQ_HOST,
            'RABBITMQ_PORT': self.RABBITMQ_PORT,
            'RABBITMQ_USER': self.RABBITMQ_USER,
            'RABBITMQ_PASSWORD': self.RABBITMQ_PASSWORD,
            'RABBITMQ_HEARTBEAT': self.RABBITMQ_HEARTBEAT,
            'RABBITMQ_BLOCKED_CONNECTION_TIMEOUT': self.RABBITMQ_BLOCKED_CONNECTION_TIMEOUT,

            'QUEUE_ML_TASKS': self.QUEUE_ML_TASKS,
        }
        for field_name, field_value in required_fields.items():
            if field_value is None:
                raise ValueError(f"Variable value '{field_name}' required")
        return self

    @property
    def log_level(self) -> int:
        if not self.LOG_LEVEL:
            return logging.INFO

        level_str = self.LOG_LEVEL.strip().upper()

        level = getattr(logging, level_str, None)
        if isinstance(level, int):
            return level

        raise ValueError(f"Invalid log level: '{self.LOG_LEVEL}' not in DEBUG, INFO, WARNING, ERROR, CRITICAL")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
