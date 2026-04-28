import os
import logging
from typing import Any, Optional, Tuple
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from datasource.config import get_settings

settings = get_settings()

logging.getLogger("pika").setLevel(logging.WARNING)

_connection_state: Tuple[Optional[int], Optional[BlockingConnection]] = (None, None)

def get_amqp_url() -> str:
    return (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
        f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
    )

def new_connection() -> BlockingConnection:
    return BlockingConnection(settings.pika_connection_parameters)

def get_connection() -> BlockingConnection:

    global _connection_state

    pid = os.getpid()
    state_pid, conn = _connection_state

    if conn is None or conn.is_closed or state_pid != pid:
        conn = new_connection()
        _connection_state = (pid, conn)

    return conn

def get_channel() -> BlockingChannel:
    return get_connection().channel()

def get_queue_ml_tasks() -> str:
    return settings.QUEUE_ML_TASKS or "ML_Tasks"

def declare_queue(queue_name: str) -> Any:
    if queue_name == "amq.rabbitmq.reply-to":
        return queue_name
    channel = get_channel()
    try:
        return channel.queue_declare(queue=queue_name,
                                     durable=True,
                                     exclusive=False,
                                     arguments={"x-queue-type": "classic"}
                                     ).method.queue
    finally:
        try:
            channel.close()
        except Exception:
            pass