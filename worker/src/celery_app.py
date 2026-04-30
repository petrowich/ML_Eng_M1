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
    # backend='rpc://',
    include=['processing'],
    task_default_queue=get_queue_ml_tasks(),
    accept_content=['application/json', 'text/plain'],
    task_serializer='json',
    result_serializer='json',
    task_acks_late=False,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    worker_send_task_events=True,
    task_track_started=True,
)

app.conf.update(
    broker_pool_limit=1,
    worker_max_tasks_per_child=10,
)
