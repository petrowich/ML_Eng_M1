import logging
from sqlalchemy import inspect, Engine
from sqlmodel import SQLModel, Session, create_engine
from datasource.config import get_settings
from models.ml_model import MLModel
from models.ml_task import MLTask, MLTaskStatus
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.user import User, UserRole, UserAuth
from services.repository.ml_model import add_ml_models
from services.repository.ml_task import add_ml_tasks
from services.repository.prediction import add_predictions
from services.repository.transaction import add_transactions
from services.repository.user import add_user, add_users, get_all_users

settings = get_settings()
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


_engine = None

def get_engine() -> Engine:
    global _engine

    if _engine is None:
        _engine = create_engine(
            url=settings.database_url_psycopg,
            echo=settings.ENGINE_ECHO_DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,)
    return _engine

def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def init_db(drop_all: bool = False):
    try:
        engine = get_engine()
        new_db = drop_all or is_new_db(engine)
        if drop_all:
            SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        if new_db:
            populate_db(engine)
    except Exception:
        raise

def is_new_db(engine: Engine) -> bool:
    inspector = inspect(engine)
    for table_name, table in SQLModel.metadata.tables.items():
        if not inspector.has_table(table_name):
            return True
    return False

def populate_db(engine: Engine):
    try:
        logging.info(f"populating db")

        # МЛ модель
        ml_model_1 = MLModel(name='Logistic Regression', reference='LOGISTIC', description='Logistic Regression Model', prediction_cost=1.05)
        ml_model_2 = MLModel(name='Decision Tree Classifier', reference='TREE', description='Decision Tree Classifier Model', prediction_cost=1.75)
        ml_model_3 = MLModel(name='Linear Regression', reference='LINEAR', description='Linear Regression Model', prediction_cost=0.50)
        ml_models = [ml_model_1, ml_model_2, ml_model_3]
        with Session(engine) as session:
            add_ml_models(ml_models, session)

        # пользователь с ролю админа
        admin = User(name='Admin', email='admin@admins.ml', role=UserRole.ADMIN, auth=UserAuth(login='admin', pwd_hash='admin'))
        with Session(engine) as session:
            add_user(admin, session)

        # пользователи
        first_user = User(name='First User', email='first@users.ml', role=UserRole.USER, auth=UserAuth(login='first', pwd_hash='qwerty'), balance=150)
        second_user = User(name='Second User', email='second@users.ml', role=UserRole.USER, balance=100)
        third_user = User(name='Third User', email='third@users.ml', role=UserRole.USER, auth=UserAuth(login='third', pwd_hash='password'), balance=195.05)
        ml_users = [first_user, second_user, third_user]
        with Session(engine) as session:
            add_users(ml_users, session)

        # транзакции
        deposit_01 = Transaction(user=first_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=100, balance=150)
        deposit_02 = Transaction(user=second_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=50, balance=185.40)
        deposit_03 = Transaction(user=third_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=150, balance=195.05)

        withdraw_01 = Transaction(user=first_user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.05, balance=150)
        withdraw_02 = Transaction(user=second_user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.75, balance=185.40)
        withdraw_03 = Transaction(user=second_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=0.50, balance=185.40)
        withdraw_04 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.75, balance=197.15)
        withdraw_05 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.05, balance=196.10)
        withdraw_06 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=0.50, balance=196.10)
        withdraw_07 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.75, balance=195.05)

        transactions = [deposit_01, deposit_02, deposit_03,
                        withdraw_01, withdraw_02, withdraw_03, withdraw_04, withdraw_05, withdraw_06, withdraw_07]
        with Session(engine) as session:
            add_transactions(transactions, session)

        # задачи для МЛ Модели
        task_01 = MLTask(user=first_user, ml_model=ml_model_1, request="request of first user", transaction=withdraw_01, status=MLTaskStatus.FAILED)
        task_02 = MLTask(user=second_user, ml_model=ml_model_2, request="first request of second user", transaction=withdraw_02, status=MLTaskStatus.COMPLETED)
        task_03 = MLTask(user=second_user, ml_model=ml_model_3, request="second request of second user", transaction=withdraw_03, status=MLTaskStatus.RUNNING)
        task_04 = MLTask(user=third_user, ml_model=ml_model_1, request="first request of third user", transaction=withdraw_04, status=MLTaskStatus.STOPPED)
        task_05 = MLTask(user=third_user, ml_model=ml_model_2, request="second request of third user", transaction=withdraw_05, status=MLTaskStatus.COMPLETED)
        task_06 = MLTask(user=third_user, ml_model=ml_model_3, request="third request of third user", transaction=withdraw_06, status=MLTaskStatus.COMPLETED)
        task_07 = MLTask(user=third_user, ml_model=ml_model_1, request="fourth request of third user", transaction=withdraw_07, status=MLTaskStatus.RUNNING)

        ml_tasks = [task_01, task_02, task_03, task_04, task_05, task_06, task_07]
        with Session(engine) as session:
            add_ml_tasks(ml_tasks, session)

        # предсказания
        prediction_01 = Prediction(result='prediction 01', ml_task=task_02, cost=1.75)
        prediction_02 = Prediction(result='prediction 02', ml_task=task_05, cost=1.75)
        prediction_03 = Prediction(result='prediction 03', ml_task=task_06, cost=0.50)

        predictions = [prediction_01, prediction_02, prediction_03]
        with Session(engine) as session:
            add_predictions(predictions, session)

        with Session(engine) as session:
            add_ml_tasks(ml_tasks, session)
            users = get_all_users(session)
            logging.info(f"number of users: {len(users)}")

    except Exception:
        raise
