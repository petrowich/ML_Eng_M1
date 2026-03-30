import uuid
from enum import Enum
from decimal import Decimal
from datetime import datetime
from abc import ABC, abstractmethod

class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class TaskStatus(Enum):
    NEW = "NEW"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class User:
    def __init__(self, user_id: int, auth: UserAuth, role: UserRole = UserRole.USER, balance: Decimal = 0.0):
        self._id: int = user_id
        self._auth: UserAuth = auth
        self._role: UserRole = role
        self._balance: Decimal = balance
        self._created = datetime.now()

    def deposit(self, amount) -> Transaction:
        self._balance += amount
        return Transaction(self, TransactionType.DEPOSIT, amount, self._balance)

    def withdraw(self, amount) -> Transaction:
        self._balance -= amount
        return Transaction(self, TransactionType.WITHDRAW, amount, self._balance)

    def get_balance(self):
        return self._balance

class UserAuth:
    def __init__(self, login, pwd_hash):
        self._login = login
        self._pwd_hash = pwd_hash

class Model(ABC):
    def __init__(self, model_id: int, name, prediction_cost: Decimal = 0.0):
        self._id: int = model_id
        self._name = name
        self._description = name
        self._prediction_cost = prediction_cost

    @abstractmethod
    def predict(self, request) -> Prediction:
        """метод выполнения предсказания"""
        pass

class Prediction:
    def __init__(self, prediction_id: int, result, cost: Decimal = 0.0):
        self._id = prediction_id
        self._result = result
        self._cost = cost
        self._created = datetime.now()

    def get_cost(self):
        return self._cost


class Task:
    def __init__(self, task_id: int, user, model, request):
        self._id = task_id
        self._user: User = user
        self._model: Model = model
        self._request = request
        self._status = TaskStatus.NEW
        self._created = datetime.now()
        self._duration_ms: int = 0
        self._prediction = None
        self._transaction = None

    def run(self):
        self._status = TaskStatus.RUNNING
        try:
            self._prediction: Prediction = self._model.predict(self._request)
        except Exception:
            self._status = TaskStatus.FAILED
            raise
        self._status = TaskStatus.COMPLETED
        self._transaction: Transaction = self._user.withdraw(self._prediction.get_cost())

class Transaction:
    def __init__(self, user, transaction_type, amount, balance):
        self._id = uuid.uuid4()
        self._user = user
        self._type = transaction_type
        self._amount = amount
        self._balance = balance
        self._timestamp = datetime.now()

class TaskHistory:
    def __init__(self):
        self._tasks: list[Task] = []

    def append(self, task: Task):
        self._tasks.append(task)