import json
import logging
import time
from typing import Any, Dict, Optional, Union

from celery_app import app
from datasource.config import get_settings
from datasource.rabbitmq import get_channel, declare_queue

from models import predict

from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


def json_load(value: Union[str, Dict[str, Any], None], field_name: str) -> Dict[str, Any]:
    if value is None:
        raise ValueError(f"{field_name} is missing in the message.")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"{field_name} must be a valid JSON string: {e}") from e
    raise ValueError(f"{field_name} must be dict or JSON string, got {type(value).__name__}")

def declare_reply_queue(reply_to: str) -> None:
    if reply_to == "amq.rabbitmq.reply-to":
        return
    declare_queue(reply_to)

@app.task(bind=True, name="process_ml_task")
def process_ml_task(self, message_body: Union[str, Dict[str, Any]]):
    reply_to = getattr(self.request, "reply_to", None)
    correlation_id = getattr(self.request, "correlation_id", None)

    if not reply_to or not correlation_id:
        logger.error("Missing reply_to/correlation_id (reply_to=%r correlation_id=%r)", reply_to, correlation_id)
        return False

    start_ns = 0

    try:
        if isinstance(message_body, dict):
            message = message_body
        else:
            message = json.loads(message_body)

        ml_task_id = message.get("ml_task_id")
        if not ml_task_id:
            raise ValueError("ml_task_id is missing in the message.")

        ml_model = message.get("ml_model")
        if not ml_model:
            raise ValueError("ml_model is missing in the message.")

        request_data = json_load(message.get("request"), "request")

        declare_reply_queue(reply_to)

        with get_channel() as channel:
            publish_response(channel, reply_to, correlation_id, ml_task_id, "RUNNING")

        start_ns = time.perf_counter_ns()

        prediction = predict(ml_model, request_data)

        with get_channel() as channel:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            publish_response(channel, reply_to, correlation_id, ml_task_id, "COMPLETED", duration_ms, prediction)

        return True

    except (AMQPConnectionError, AMQPChannelError) as e:
        logger.exception("RabbitMQ error while processing task: %s", e)
        return False

    except Exception as e:
        try:
            if reply_to and correlation_id:
                with get_channel() as channel:
                    duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
                    publish_response(channel, reply_to, correlation_id, message.get("ml_task_id"), "FAILED", duration_ms, failure=str(e))
        except Exception:
            logger.exception("Failed to publish FAILED status to reply queue")

        logger.exception("Failed to process task")
        return False


def publish_response(
    channel: BlockingChannel,
    reply_to: str,
    correlation_id: str,
    ml_task_id: Any,
    status: str,
    duration_ms: float = 0.0,
    prediction: Optional[Any] = None,
    failure: Optional[str] = None,
) -> None:
    response_body = {
        "ml_task_id": ml_task_id,
        "status": status,
        "duration_ms": duration_ms,
        "prediction": prediction,
        "failure": failure,
    }

    channel.basic_publish(
        exchange="",
        routing_key=reply_to,
        body=json.dumps(response_body, ensure_ascii=False).encode("utf-8"),
        properties=BasicProperties(
            correlation_id=correlation_id,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=2,
        ),
    )
    