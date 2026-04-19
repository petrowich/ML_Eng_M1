import logging
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

def get_rmq_connection() -> BlockingConnection:
    global _connection

    if _connection is None or _connection.is_closed:
        _connection = BlockingConnection(settings.pika_connection_parameters)

    return _connection

def get_rmq_channel() -> BlockingChannel:
    connection = get_rmq_connection()
    return connection.channel()

def get_queue_ml_tasks() -> str:
    return settings.QUEUE_ML_TASKS or 'ML_Tasks'

def get_queue_predictions() -> str:
    return settings.QUEUE_PREDICTIONS or 'Predictions'

def declare_queue(queue_name: str):
    connection = get_rmq_connection()
    with connection.channel() as channel:
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={'x-producers-type': 'classic'}
        )
