from datasource.config import get_settings

settings = get_settings()

def get_amqp_url() -> str:
    return (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
        f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
    )

def get_queue_ml_tasks() -> str:
    return settings.QUEUE_ML_TASKS or "ML_Tasks"
