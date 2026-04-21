import logging
from typing import Any

from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

from datasource.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("pika.channel").setLevel(logging.WARNING)
logging.getLogger("pika.connection").setLevel(logging.WARNING)
logging.getLogger("pika.adapters.blocking_connection").setLevel(logging.WARNING)

_connection = None

def get_amqp_url() -> str:
    return f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//'

def get_connection() -> BlockingConnection:
    global _connection

    if _connection is None or _connection.is_closed:
        _connection = BlockingConnection(settings.pika_connection_parameters)

    return _connection

def get_channel() -> BlockingChannel:
    connection = get_connection()
    return connection.channel()

def get_queue_ml_tasks() -> str:
    return settings.QUEUE_ML_TASKS or 'ML_Tasks'

def declare_queue(queue_name: str) -> Any:
    connection = get_connection()
    with connection.channel() as channel:
        return channel.queue_declare(
            queue=queue_name,
            durable=True,
            exclusive=False,
            arguments={'x-producers-type': 'classic'}
        ).method.queue