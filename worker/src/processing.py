import json
import logging
import time
from typing import Any, Dict, Union
from celery_app import app
from datasource.config import get_settings
from models import predict
from pika import BasicProperties
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

@app.task(bind=True, name="ml_task", acks_late=True, reject_on_worker_lost=True)
def process_ml_task(self, message_body: Union[str, Dict[str, Any]]):
    logger.info(f"Starting processing request id:[{self.request.id}] message:{message_body} by worker {self.request.hostname}")

    reply_to = getattr(self.request, "reply_to", None)
    correlation_id = getattr(self.request, "correlation_id", None)

    if not reply_to or not correlation_id:
        logger.error(f"Missing reply_to/correlation_id (reply_to: {reply_to} correlation_id: {correlation_id})")
        return False

    try:
        if isinstance(message_body, dict):
            message = message_body
        else:
            message = json.loads(message_body)

        ml_task_id = message.get("ml_task_id")
        if not ml_task_id:
            raise ValueError("ml_task_id is missing in the message.")

        ml_model = message.get("ml_model","")
        if not ml_model:
            raise ValueError("ml_model is missing in the message.")

        publish(self.app, reply_to, correlation_id, ml_task_id, status="RUNNING", duration_ms=0.0, prediction=None, failure=None)

        start_ns = 0.0
        prediction = None
        failure = None
        try:
            start_ns = time.perf_counter_ns()
            request_data = json_load(message.get("request"), "request")
            prediction = predict(ml_model, request_data)
            status = "COMPLETED"
        except Exception as e:
            failure = str(e)
            status="FAILED"
        finally:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        return publish(self.app, reply_to, correlation_id, ml_task_id, status, duration_ms, prediction, failure)

    except (AMQPConnectionError, AMQPChannelError) as e:
        logger.exception("RabbitMQ error while processing task: %s", e)
        return False
    except Exception as e:
        logger.exception(f"Failed to process task: {e}")
        return False

def publish(celery_app: "Celery", reply_to, correlation_id, ml_task_id, status, duration_ms: float, prediction = None, failure = None) -> bool:
    if not reply_to or reply_to == "amq.rabbitmq.reply-to":
        return False
    try:
        response_body = {
            "ml_task_id": ml_task_id,
            "status": status,
            "duration_ms": duration_ms,
            "prediction": prediction,
            "failure": failure,
            "correlation_id": correlation_id,
        }

        with celery_app.producer_pool.acquire(block=True) as producer:
            producer.publish(
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

        logger.info(f"Published status {status} for task {ml_task_id} successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to publish status {status} for task {ml_task_id}: {e}")
        return False
