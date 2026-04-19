import json
import logging
import time
import uuid
from typing import Optional, Dict

from models.ml_task import MLTask
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from pika.adapters.blocking_connection import BlockingConnection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def process_ml_task(ml_task: MLTask, request_queue: str, response_queue: str, rmq_connection: BlockingConnection) -> Optional[Dict]:
    if not ml_task:
        raise Exception(f"ML task is not defined")

    if ml_task.ml_model:
        ml_model = ml_task.ml_model
    else:
        raise Exception(f"ML model is not defined")

    try:
        message = {
            "ml_task_id": ml_task.id,
            "ml_model": ml_model.reference,
            "request": ml_task.request,
        }

        task_id = str(uuid.uuid4())
        task_name = 'process_ml_task'
        args = [json.dumps(message, ensure_ascii=False)]

        body_dict = {
            "id": task_id,
            "task": task_name,
            "args": args,
            "kwargs": {}
        }

        correlation_id = str(uuid.uuid4())
        response = None
        with rmq_connection.channel() as channel:
            properties = BasicProperties(
                delivery_mode=2,
                content_type='application/json',
                content_encoding='utf-8',
                reply_to=channel.queue_declare(queue=response_queue, durable=True, exclusive=False).method.queue,
                correlation_id=correlation_id,
                headers={'task': task_name, 'id': task_id}
            )

            channel.basic_publish(
                exchange='',
                routing_key=request_queue,
                body=json.dumps(body_dict, ensure_ascii=False).encode('utf-8'),
                properties=properties
            )

            logger.info(f"ML task id={ml_task.id} sent to queue '{request_queue}')")

            def on_response(ch, method, props, body):
                nonlocal response
                if props.correlation_id == correlation_id:
                    response = json.loads(body.decode('utf-8'))
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=response_queue, on_message_callback=on_response, auto_ack=False)

            start_time = time.time()
            step_timeout = 1
            timeout = 30
            while response is None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise TimeoutError("RPC timeout")
                remaining = timeout - elapsed
                channel.connection.process_data_events(time_limit=min(step_timeout, remaining))

        logger.info(f"Received response: {response}")
        return response

    except (AMQPConnectionError, AMQPChannelError) as e:
        print(f"RabbitMQ connection error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Failed to send ML task id={ml_task.id} to queue '{request_queue}': {e}")
        raise e
