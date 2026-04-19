import logging
from celery_app import app
from datasource.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

argv = [
    'worker',
    f'--loglevel={settings.LOG_LEVEL}',
    '-Q', settings.input_queue,
    '-P', 'solo',
    # '--concurrency=4', '--hostname=localhost'
]

if __name__ == '__main__':
    logger.info(f'Starting celery worker with args: {argv}')
    try:
        app.worker_main(argv)
    except Exception as e:
        logger.error(e)