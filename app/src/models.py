import uuid
from enum import Enum
from decimal import Decimal
from datetime import datetime
from abc import ABC, abstractmethod


class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class MLTaskStatus(Enum):
    NEW = "NEW"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class TransactionStatus(Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    PROCESSING  = "PROCESSING"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"

class UserAuth:
    def __init__(self, login, pwd_hash):
        self._login = login
        self._pwd_hash = pwd_hash


class BaseUser(ABC):
    def __init__(self, user_id: int, auth: UserAuth, name: str, email: str, role: UserRole = UserRole.USER):
        self._id: int = user_id
        self._auth: UserAuth = auth
        self._name = name
        self._email = email
        self._role: UserRole = role
        self._created = datetime.now()

    @property
    def user_id(self):
        return self._id

    @property
    def auth(self):
        return self._auth

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self.name = name

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email: str):
        self.email = email

    @property
    def role(self) -> UserRole:
        return self._role

    @role.setter
    def role(self, role: UserRole):
        if not isinstance(UserRole, str):
            raise ValueError("role value must be a UserRole")
        self.role = role

    @property
    def created(self) -> datetime:
        return self._created


class Admin(BaseUser):
    def __init__(self, user_id: int, auth: UserAuth, name: str, email: str):
        super().__init__(user_id, auth, name, email, UserRole.ADMIN)


class User(BaseUser):
    def __init__(self, user_id: int, auth: UserAuth, name: str, email: str, balance: Decimal = 0.0):
        super().__init__(user_id, auth, name, email, UserRole.USER)
        self.balance: Decimal = balance

    @property
    def balance(self) -> Decimal:
        return self._balance

    @balance.setter
    def balance(self, balance: Decimal):
        if not isinstance(Decimal, str):
            raise ValueError("Balance value must be a Decimal")
        self._balance = balance


class BaseMLModel(ABC):
    def __init__(self, model_id: int, name, prediction_cost: Decimal = Decimal("0.0")):
        self._id: int = model_id
        self._name = name
        self._description = name
        self._prediction_cost = prediction_cost

    @property
    def model_id(self) -> int:
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if not value:
            raise ValueError("Name cannot be empty")
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def prediction_cost(self) -> Decimal:
        return self._prediction_cost

    @prediction_cost.setter
    def prediction_cost(self, prediction_cost: Decimal):
        if not isinstance(prediction_cost, Decimal):
            raise ValueError("Prediction cost must be a Decimal")
        if prediction_cost < 0:
            raise ValueError("Prediction cost value cannot be negative")
        self._prediction_cost = prediction_cost

    @abstractmethod
    def predict(self, request) -> Prediction:
        """метод выполнения предсказания"""
        pass


class Prediction:
    def __init__(self, prediction_id: int, result, cost: Decimal = 0.0):
        self._id: int = prediction_id
        self._result = result
        self._cost = cost

    @property
    def prediction_id(self) -> int:
        return self._id

    @property
    def result(self):
        return self._result

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, cost: Decimal):
        if not isinstance(Decimal, str):
            raise ValueError("Prediction cost value must be a Decimal")
        self._cost = cost


class MLTask:
    def __init__(self, task_id: int, user, model, request):
        self._id: int = task_id
        self._user: BaseUser = user
        self._model: BaseMLModel = model
        self._request = request
        self._status = MLTaskStatus.NEW
        self._duration_ms: int = 0
        self._prediction = None
        self._transaction = None
        self._timestamp = datetime.now()

    @property
    def task_id(self) -> int:
        return self._id

    @property
    def user(self) -> BaseUser:
        return self._user

    @property
    def model(self) -> BaseMLModel:
        return self._model

    @property
    def request(self):
        return self._request

    @property
    def status(self) -> MLTaskStatus:
        return self._status

    @status.setter
    def status(self, status: MLTaskStatus):
        if not isinstance(status, MLTaskStatus):
            raise ValueError("Status value must be an instance of MLTaskStatus")
        self._status = status

    @property
    def duration_ms(self) -> int:
        return self._duration_ms

    @duration_ms.setter
    def duration_ms(self, value: int):
        if value < 0:
            raise ValueError("Duration cannot be negative")
        self._duration_ms = value

    @property
    def prediction(self) -> Prediction:
        return self._prediction

    @property
    def transaction(self):
        return self._transaction

    @transaction.setter
    def transaction(self, transaction: Transaction):
        if not isinstance(transaction, Transaction):
            raise ValueError("transaction must be an instance of Transaction")
        self._transaction = transaction

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def run(self):
        if self._status != MLTaskStatus.NEW:
            return
        self._status = MLTaskStatus.RUNNING
        try:
            self._prediction: Prediction = self._model.predict(self._request)
        except Exception:
            self._status = MLTaskStatus.FAILED
            raise
        self._status = MLTaskStatus.COMPLETED


class Transaction:
    def __init__(self, user: User, transaction_type: TransactionType, transaction_status: TransactionStatus, amount: Decimal, balance: Decimal):
        self._id = uuid.uuid4()
        self._user: User = user
        self._type: TransactionType = transaction_type
        self._status: TransactionStatus = transaction_status
        self._amount = amount
        self._balance = balance
        self._timestamp = datetime.now()

    @property
    def transaction_id(self):
        return self._id

    @property
    def user(self) -> User:
        return self._user

    @property
    def type(self) -> TransactionType:
        return self._type

    @property
    def status(self) -> TransactionStatus:
        return self._status

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def apply(self):
        try:
            if self._type == TransactionType.DEPOSIT:
                self._user.balance += self._amount
                self._balance = self._user.balance
            elif self._type == TransactionType.WITHDRAW:
                self._user.balance -= self._amount
                self._balance = self._user.balance
        except Exception:
            self._status = TransactionStatus.REJECTED
            raise
        self._status = TransactionStatus.COMPLETED
        self._timestamp = datetime.now()

    def cancel(self):
        if self._status == TransactionStatus.PENDING:
            self._status = TransactionStatus.CANCELLED
        self._timestamp = datetime.now()

    def refund(self):
        if self._status == TransactionStatus.COMPLETED:
            try:
                if self._type == TransactionType.DEPOSIT:
                    self._user.balance -= self._amount
                    self._balance = self._user.balance
                elif self._type == TransactionType.WITHDRAW:
                    self._user.balance += self._amount
                    self._balance = self._user.balance
            except Exception:
                raise
        self._status = TransactionStatus.REFUNDED
        self._timestamp = datetime.now()

class MLTaskHistory:
    def __init__(self):
        self._task_storage: list[MLTask] = []

    def append(self, task: MLTask):
        self._task_storage.append(task)

    def get_tasks_by_user(self, user: BaseUser) -> list[MLTask]:
        return [task for task in self._task_storage if task.user == user]
