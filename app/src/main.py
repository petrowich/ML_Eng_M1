from sqlmodel import Session

from database.config import get_settings
from database.database import init_db, get_engine
from models.ml_task import MLTask, MLTaskStatus
from models.ml_model import MLModel
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.user import UserAuth
from models.ml_user import MLAdmin, MLUser
from services.ml_admin import create_admin
from services.ml_model import create_ml_model
from services.ml_task import create_ml_tasks
from services.ml_user import create_users, get_all_users
from services.predictions import create_predictions, get_predictions_by_user
from services.transaktions import create_transactions, get_completed_withdraw_transactions_by_user, apply_transaction
from services.user import get_user_by_id

settings = get_settings()

if __name__ == '__main__':
    init_db(drop_all=True)
    print('db has been inited')

    engine = get_engine()

    # МЛ модель
    ml_model = MLModel(name='ML Model', description='greatest ml model ever', prediction_cost=1.05)
    with Session(engine) as session:
        create_ml_model(ml_model, session)

    # пользователь с ролю админа
    admin = MLAdmin(name='Admin', email='admin@admins.ml', auth=UserAuth(login='admin', pwd_hash='admin'))
    with Session(engine) as session:
        create_admin(admin, session)

    # пользователи
    first_user = MLUser(name='First User', email='first@users.ml', auth=UserAuth(login='first', pwd_hash='qwerty'), balance=150)
    second_user = MLUser(name='Second User', email='second@users.ml', balance=100)
    third_user = MLUser(name='Third User', email='third@users.ml', auth=UserAuth(login='third', pwd_hash='password'), balance=195.05)
    ml_users = [first_user, second_user, third_user]
    with Session(engine) as session:
        create_users(ml_users, session)

    # предсказания
    prediction_01 = Prediction(result='prediction 01 result', cost=1.05)
    prediction_02 = Prediction(result='prediction 02 result', cost=1.05)
    prediction_03 = Prediction(result='prediction 03 result', cost=1.05)

    predictions = [prediction_01, prediction_02, prediction_03]
    with Session(engine) as session:
        create_predictions(predictions, session)

    # транзакции
    deposit_01 = Transaction(user=first_user.user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=100, balance=150)
    deposit_02 = Transaction(user=second_user.user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=50, balance=185.40)
    deposit_03 = Transaction(user=third_user.user, type=TransactionType.DEPOSIT, status=TransactionStatus.COMPLETED, amount=150, balance=195.05)

    withdraw_01 = Transaction(user=first_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.05, balance=150)
    withdraw_02 = Transaction(user=second_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.05, balance=185.40)
    withdraw_03 = Transaction(user=second_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=185.40)
    withdraw_04 = Transaction(user=third_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.CANCELLED, amount=1.05, balance=197.15)
    withdraw_05 = Transaction(user=third_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.COMPLETED, amount=1.05, balance=196.10)
    withdraw_06 = Transaction(user=third_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=196.10)
    withdraw_07 = Transaction(user=third_user.user, type=TransactionType.WITHDRAW, status=TransactionStatus.PENDING, amount=1.05, balance=195.05)

    transactions = [deposit_01, deposit_02, deposit_03,
                    withdraw_01, withdraw_02, withdraw_03, withdraw_04, withdraw_05, withdraw_06, withdraw_07]
    with Session(engine) as session:
        create_transactions(transactions, session)

    # задачи для МЛ Модели
    task_01 = MLTask(user=first_user.user, model=ml_model, request="request of first user", transaction=withdraw_01, status=MLTaskStatus.FAILED)
    task_02 = MLTask(user=second_user.user, model=ml_model, request="first request of second user", transaction=withdraw_02, status=MLTaskStatus.COMPLETED, prediction=prediction_01)
    task_03 = MLTask(user=second_user.user, model=ml_model, request="second request of second user", transaction=withdraw_03, status=MLTaskStatus.RUNNING)
    task_04 = MLTask(user=third_user.user, model=ml_model, request="first request of third user", transaction=withdraw_04, status=MLTaskStatus.STOPPED)
    task_05 = MLTask(user=third_user.user, model=ml_model, request="second request of third user", transaction=withdraw_05, status=MLTaskStatus.COMPLETED, prediction=prediction_02)
    task_06 = MLTask(user=third_user.user, model=ml_model, request="third request of third user", transaction=withdraw_06, status=MLTaskStatus.COMPLETED, prediction=prediction_03)
    task_07 = MLTask(user=third_user.user, model=ml_model, request="fourth request of third user", transaction=withdraw_07, status=MLTaskStatus.RUNNING)

    ml_tasks = [task_01, task_02, task_03, task_04, task_05, task_06, task_07]
    with Session(engine) as session:
        create_ml_tasks(ml_tasks, session)

    print('db has been populated')

    # расчёт расходов по пользователям
    print('\ntotal by users')
    with Session(engine) as session:
        for ml_user in get_all_users(session):
            predictions = get_predictions_by_user(ml_user.user, session)
            transactions = get_completed_withdraw_transactions_by_user(ml_user.user, session)
            expenses = sum(prediction.cost for prediction in predictions)
            payed = sum(transaction.amount for transaction in transactions)
            print(f"{ml_user.user.name}: predictions={len(predictions)} expenses={expenses} payed={payed}")

    # проведение транзакции
    print('\napplying transaction')
    with Session(engine) as session:
        user = get_user_by_id(withdraw_06.user_id, session)
        print(f"{user.name} balance before {user.balance}")
        print(f"start applying transaction {withdraw_06}")
        apply_transaction(withdraw_06, session)
        print(f"completed transaction {withdraw_06}")
        print(f"transaction {withdraw_06}")
        user = get_user_by_id(withdraw_06.user_id, session)
        print(f"{user.name} balance after {user.balance}")
