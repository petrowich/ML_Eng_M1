import logging
from sqlalchemy import inspect
from sqlmodel import SQLModel, Session, create_engine
from database.config import get_settings
from models.ml_model import MLModel
from models.ml_task import MLTask, MLTaskStatus
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.user import User, UserRole, UserAuth
from services.ml_model import create_ml_model
from services.ml_task import create_ml_tasks
from services.prediction import create_predictions
from services.transaction import create_transactions
from services.user import create_user, create_users, get_all_users


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_engine():
    settings = get_settings()

    engine = create_engine(
        url=settings.database_url_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    return engine

def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def init_db(drop_all: bool = False, populate: bool = False):
    try:
        engine = get_engine()
        new_db = drop_all or is_new_db(engine)
        if drop_all:
            SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        if populate and new_db:
            populate_db(engine)
    except Exception:
        raise

def is_new_db(engine) -> bool:
    inspector = inspect(engine)
    for table_name, table in SQLModel.metadata.tables.items():
        if not inspector.has_table(table_name):
            return True
    return False

def populate_db(engine):
    try:
        logging.info(f"populating db")

        # МЛ модель
        ml_model = MLModel(name='ML Model', description='The Greatest ML Model Ever', prediction_cost=1.05)
        with Session(engine) as session:
            create_ml_model(ml_model, session)

        # пользователь с ролю админа
        admin = User(name='Admin', email='admin@admins.ml', role=UserRole.ADMIN, auth=UserAuth(login='admin', pwd_hash='admin'))
        with Session(engine) as session:
            create_user(admin, session)

        # пользователи
        first_user = User(name='First User', email='first@users.ml', role=UserRole.USER, auth=UserAuth(login='first', pwd_hash='qwerty'), balance=150)
        second_user = User(name='Second User', email='second@users.ml', role=UserRole.USER, balance=100)
        third_user = User(name='Third User', email='third@users.ml', role=UserRole.USER, auth=UserAuth(login='third', pwd_hash='password'), balance=195.05)
        ml_users = [first_user, second_user, third_user]
        with Session(engine) as session:
            create_users(ml_users, session)

        # предсказания
        prediction_01 = Prediction(result='prediction 01', cost=1.05)
        prediction_02 = Prediction(result='prediction 02', cost=1.05)
        prediction_03 = Prediction(result='prediction 03', cost=1.05)

        predictions = [prediction_01, prediction_02, prediction_03]
        with Session(engine) as session:
            create_predictions(predictions, session)

        # транзакции
        deposit_01 = Transaction(user=first_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=100, balance=150)
        deposit_02 = Transaction(user=second_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=50, balance=185.40)
        deposit_03 = Transaction(user=third_user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=150, balance=195.05)

        withdraw_01 = Transaction(user=first_user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.05, balance=150)
        withdraw_02 = Transaction(user=second_user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.05, balance=185.40)
        withdraw_03 = Transaction(user=second_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=185.40)
        withdraw_04 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.05, balance=197.15)
        withdraw_05 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.05, balance=196.10)
        withdraw_06 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=196.10)
        withdraw_07 = Transaction(user=third_user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=195.05)

        transactions = [deposit_01, deposit_02, deposit_03,
                        withdraw_01, withdraw_02, withdraw_03, withdraw_04, withdraw_05, withdraw_06, withdraw_07]
        with Session(engine) as session:
            create_transactions(transactions, session)

        # задачи для МЛ Модели
        task_01 = MLTask(user=first_user, model=ml_model, request="request of first user", transaction=withdraw_01, status=MLTaskStatus.FAILED)
        task_02 = MLTask(user=second_user, model=ml_model, request="first request of second user", transaction=withdraw_02, status=MLTaskStatus.COMPLETED, prediction=prediction_01)
        task_03 = MLTask(user=second_user, model=ml_model, request="second request of second user", transaction=withdraw_03, status=MLTaskStatus.RUNNING)
        task_04 = MLTask(user=third_user, model=ml_model, request="first request of third user", transaction=withdraw_04, status=MLTaskStatus.STOPPED)
        task_05 = MLTask(user=third_user, model=ml_model, request="second request of third user", transaction=withdraw_05, status=MLTaskStatus.COMPLETED, prediction=prediction_02)
        task_06 = MLTask(user=third_user, model=ml_model, request="third request of third user", transaction=withdraw_06, status=MLTaskStatus.COMPLETED, prediction=prediction_03)
        task_07 = MLTask(user=third_user, model=ml_model, request="fourth request of third user", transaction=withdraw_07, status=MLTaskStatus.RUNNING)

        ml_tasks = [task_01, task_02, task_03, task_04, task_05, task_06, task_07]
        with Session(engine) as session:
            create_ml_tasks(ml_tasks, session)

        with Session(engine) as session:
            create_ml_tasks(ml_tasks, session)
            users = get_all_users(session)
            logging.info(f"number of users: {len(users)}")

    except Exception:
        raise
