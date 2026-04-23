import json
import logging
import threading
import time
from sqlalchemy import Engine
import services.repository.ml_model
import services.repository.ml_task
import services.repository.prediction
import services.repository.transaction
from pika import ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPConnectionError
from pika.spec import Basic, BasicProperties
from sqlmodel import Session, create_engine
from datasource.config import get_settings
from datasource.rabbitmq import get_queue_predictions, declare_queue
from models.ml_task import MLTaskStatus
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

settings = get_settings()


class PredictionConsumer:
    def __init__(self, amqp_param: ConnectionParameters, db_url, db_echo):
        self._amqp_param: ConnectionParameters = amqp_param
        self._db_url = db_url
        self._db_echo = db_echo
        self._connection: BlockingConnection | None
        self._channel: BlockingChannel | None = None
        self._consumer_thread: threading.Thread | None = None
        self._engine: Engine | None = None
        self._stop_event = threading.Event()
        self.queue=get_queue_predictions()

    def _callback(self, channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        try:
            data: dict = json.loads(body.decode("utf-8"))

            ml_task_id = data.get("ml_task_id")
            if not ml_task_id or not isinstance(ml_task_id, int):
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return

            ml_task_id = int(ml_task_id)
            status = MLTaskStatus(data.get("status"))
            duration_ms = data.get("duration_ms")
            result = data.get("prediction")
            failure = data.get("failure")
            ml_model_id = None
            user_id = None

            with Session(self._engine) as session:
                ml_task = services.repository.ml_task.get_ml_task_by_id(ml_task_id, session)
                ml_model_id = ml_task.ml_model_id
                user_id = ml_task.user_id
                ml_task.status = status
                ml_task.failure = failure
                if duration_ms and isinstance(duration_ms, int):
                    ml_task.duration_ms = int(duration_ms)
                logger.info(f"ML task status received ml_task_id={ml_task_id} → {status}")
                services.repository.ml_task.add_ml_task(ml_task, session)

            if status == MLTaskStatus.COMPLETED:
                with Session(self._engine) as session:
                    logger.info(f"prediction received ml_task_id={ml_task_id}: '{result}'")

                    ml_task = services.repository.ml_task.get_ml_task_by_id(ml_task_id, session)
                    ml_model = services.repository.ml_model.get_ml_model_by_id(ml_model_id, session)
                    user = services.repository.user.get_user_by_id(user_id, session)
                    cost = ml_model.prediction_cost

                    try:
                        prediction = Prediction(result=result, ml_task=ml_task, cost=cost)
                        services.repository.prediction.add_prediction(prediction, session)

                        withdraw = Transaction(user=user, type=TransactionType.WITHDRAW, amount=cost)
                        services.repository.transaction.add_transaction(withdraw, session)
                        logger.info(f"withdraw prediction cost: {cost}")

                        services.repository.transaction.apply_transaction(withdraw, session)
                        logger.info(f"apply transaction: {withdraw}")
                    except Exception as e:
                        logger.error(f"{e}")
                        session.rollback()

            elif status == MLTaskStatus.FAILED:
                logger.info(f"prediction failure ml_task_id={ml_task_id}: '{failure}'")

            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing prediction message: {e}", exc_info=True)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _consume(self):
        while not self._stop_event.is_set():
            try:
                self._engine = create_engine(url=self._db_url, echo=self._db_echo)
                self._connection = BlockingConnection(self._amqp_param)
                self._channel = self._connection.channel()

                declare_queue(get_queue_predictions())
                self._channel.basic_qos(prefetch_count=20)
                self._channel.basic_consume(
                    queue=self.queue,
                    on_message_callback=self._callback,
                    auto_ack=False
                )
                logger.info(f"consumer started, listening on queue: {self.queue}")
                self._channel.start_consuming()

            except AMQPConnectionError as e:
                logger.error(f"RabbitMQ connection error: {e}. Reconnecting in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
                time.sleep(5)
            finally:
                self._close_connection()

    def _close_connection(self):
        if self._channel and not self._channel.is_closed:
            try:
                self._channel.close()
            except Exception as e:
                logger.error(f"close channel error: {e}")
                pass
        if self._connection and not self._connection.is_closed:
            try:
                self._connection.close()
            except Exception as e:
                logger.error(f"close connection error: {e}")
                pass

    def start(self):
        if self._consumer_thread and self._consumer_thread.is_alive():
            logger.warning("consumer is already running")
            return

        self._stop_event.clear()
        self._consumer_thread = threading.Thread(target=self._consume, daemon=True)
        self._consumer_thread.start()
        logger.info("consumer thread started")

    def stop(self, timeout: float = 10.0) -> None:
        logger.info("stopping consumer")
        self._stop_event.set()

        try:
            if self._connection and self._connection.is_open and self._channel and self._channel.is_open:
                self._connection.add_callback_threadsafe(self._channel.stop_consuming)
        except Exception:
            logger.exception("Failed to stop consuming gracefully")

        if self._consumer_thread:
            self._consumer_thread.join(timeout=timeout)

        self._close_connection()

        logger.info("consumer stopped")

prediction_consumer = PredictionConsumer(amqp_param=settings.pika_connection_parameters,
                                         db_url=settings.database_url_psycopg,
                                         db_echo=settings.ENGINE_ECHO_DEBUG
                                         )
