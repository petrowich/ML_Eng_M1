import json
import logging
import random
import time
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from datasource.config import get_settings
from celery_app import app

from datasource.rabbitmq import get_channel

settings = get_settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

@app.task(bind=True, name='process_ml_task')
def process_ml_task(self, message_body):
    try:
        logging.info(f"Processing ML task: {message_body}")

        message = json.loads(message_body)
        ml_task_id = message.get('ml_task_id')
        ml_model = message.get('ml_model')
        request_data = message.get('request')

        if not all([ml_task_id, ml_model, request_data]):
            raise ValueError("Missing required fields in message")

        prediction = ml_model_stub(ml_model, request_data)

        response_message = {
            "ml_task_id": ml_task_id,
            "prediction": prediction
        }

        reply_to = self.request.reply_to
        correlation_id = self.request.correlation_id

        if not reply_to or not correlation_id:
            raise ValueError("Missing reply_to or correlation_id in task properties")

        channel = get_channel()
        channel.queue_declare(queue=reply_to, durable=True)

        response_body_str = json.dumps(response_message, ensure_ascii=False)
        response_body = response_body_str.encode('utf-8')

        channel.basic_publish(
            exchange='',
            routing_key=reply_to,
            body=response_body,
            properties=BasicProperties(
                correlation_id=correlation_id,
                content_type='text/plain',
                content_encoding='utf-8',
                delivery_mode=2
            )
        )

    except (AMQPConnectionError, AMQPChannelError) as e:
        print(f"RabbitMQ connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to process': {e}")
        return False

def ml_model_stub(model, request):
    prediction = f"Predicted: {request} using model {model}"
    seconds = random.randint(1, 5)
    logger.info(f"Processing will take {seconds} seconds")
    logger.info(f"Processing start!")
    time.sleep(seconds)
    logger.info("Processing complete!")
    logger.info(prediction)
    return prediction
