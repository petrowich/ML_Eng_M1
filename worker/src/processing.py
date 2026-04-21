import json
import logging
import time

from pika.adapters.blocking_connection import BlockingChannel

from models import predict
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from datasource.config import get_settings
from celery_app import app

from datasource.rabbitmq import get_channel, declare_queue

settings = get_settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

@app.task(bind=True, name='process_ml_task')
def process_ml_task(self, message_body):
    try:
        reply_to = self.request.reply_to
        correlation_id = self.request.correlation_id

        if not reply_to or not correlation_id:
            raise ValueError("Missing reply_to or correlation_id in task properties")

        logging.info(f"Processing ML task: {message_body}")
        message = json.loads(message_body)

        ml_task_id = message.get('ml_task_id')
        if not ml_task_id:
            raise ValueError("ml_task_id is missing in the message.")

        declare_queue(reply_to)

        with get_channel() as channel:

            publish_response(channel, reply_to, correlation_id, ml_task_id, 'RUNNING')

            try:
                ml_model = message.get('ml_model')
                if not ml_task_id:
                    raise ValueError("ml_model is missing in the message.")

                request = message.get('request')
                if request:
                    request_data = json.loads(request)
                    prediction_start = time.perf_counter()
                    prediction = predict(ml_model, request_data)
                    prediction_end = time.perf_counter()
                    duration_ms = (prediction_end - prediction_start) * 1000
                else:
                    raise ValueError("ml_model is missing in the message.")
            except Exception as e:
                publish_response(channel, reply_to, correlation_id, ml_task_id, 'FAILED', failure=str(e))
                raise

            publish_response(channel, reply_to, correlation_id, ml_task_id, 'COMPLETED', duration_ms, prediction)

    except (AMQPConnectionError, AMQPChannelError) as e:
        print(f"RabbitMQ connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to process': {e}")
        return False

def publish_response(channel: BlockingChannel,
                     reply_to, correlation_id,
                     ml_task_id,
                     status: str,
                     duration_ms: float = 0,
                     prediction: str = None,
                     failure: str = None):
        response_body = {"ml_task_id": ml_task_id,
                         "status": status,
                         "duration_ms": duration_ms,
                         "prediction": str(prediction),
                         "failure": failure}
        response_body_json = json.dumps(response_body, ensure_ascii=False).encode('utf-8')
        channel.basic_publish(
        exchange='',
        routing_key=reply_to,
        body=response_body_json,
        properties=BasicProperties(
            correlation_id=correlation_id,
            content_type='text/plain',
            content_encoding='utf-8',
            delivery_mode=2
        )
    )