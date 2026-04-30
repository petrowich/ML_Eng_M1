import logging
from typing import Any
from pika import BlockingConnection
from contextlib import contextmanager
from datasource.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("pika.channel").setLevel(logging.WARNING)
logging.getLogger("pika.connection").setLevel(logging.WARNING)
logging.getLogger("pika.adapters.blocking_connection").setLevel(logging.WARNING)

def get_connection() -> BlockingConnection:
    return BlockingConnection(settings.pika_connection_parameters)

@contextmanager
def get_channel():
    connection = get_connection()
    channel = connection.channel()
    try:
        yield channel
    finally:
        try:
            channel.close()
        finally:
            connection.close()

def get_queue_ml_tasks() -> str:
    return settings.QUEUE_ML_TASKS or 'ML_Tasks'

def get_queue_predictions() -> str:
    return settings.QUEUE_PREDICTIONS or 'Predictions'

def declare_queue(queue_name: str) -> Any:
    connection = get_connection()
    with connection.channel() as channel:
        return channel.queue_declare(
            queue=queue_name,
            durable=True,
            exclusive=False,
            arguments={'x-producers-type': 'classic'}
        ).method.queue
