import json
import logging
from celery import Celery
from datasource.config import get_settings
from datasource.rabbitmq import get_amqp_url, get_queue_ml_tasks

settings = get_settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

app = Celery(
    settings.APP_NAME,
    broker=get_amqp_url(),
    backend='rpc://',
    include=['processing'],
    task_default_queue=get_queue_ml_tasks(),
    accept_content=['application/json', 'text/plain'],
    task_serializer='json',
    result_serializer='json'
)

if __name__ == '__main__':
    from processing import process_ml_task
    message = json.dumps({"task_id": 1001, "model": "MODEL_TEST", "request": "test request"})
    process_ml_task.delay(message)
