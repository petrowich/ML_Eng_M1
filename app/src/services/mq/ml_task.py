import json
import logging
import uuid

from datasource.rabbitmq import declare_queue, get_queue_ml_tasks, get_queue_predictions, get_channel
from models.ml_model import MLModel
from models.ml_task import MLTask
from pika import BasicProperties

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def publish_ml_task(ml_task: MLTask) -> str:
    ml_model: MLModel | None = ml_task.ml_model
    message = {
        "ml_task_id": ml_task.id,
        "ml_model": ml_model.reference if ml_model else None,
        "request": ml_task.request,
    }

    task_id = str(uuid.uuid4())
    task_name = "ml_task"
    args = [json.dumps(message, ensure_ascii=False)]

    body_dict = {
        "id": task_id,
        "task": task_name,
        "args": args,
        "kwargs": {}
    }

    correlation_id = str(uuid.uuid4())
    response_queue = get_queue_predictions()
    request_queue = get_queue_ml_tasks()

    properties = BasicProperties(
        delivery_mode=2,
        content_type='application/json',
        content_encoding='utf-8',
        reply_to=declare_queue(response_queue),
        correlation_id=correlation_id,
        headers={'task': task_name, 'id': task_id}
    )

    with get_channel() as channel:
        channel.basic_publish(
            exchange='',
            routing_key=request_queue,
            body=json.dumps(body_dict, ensure_ascii=False).encode('utf-8'),
            properties=properties
        )
    return correlation_id
