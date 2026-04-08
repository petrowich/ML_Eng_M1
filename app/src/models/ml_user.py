"""
В этом модуле содержатся классы-обёртки для модели User

Из-за проблемы наследования моделей SQLModel не удалось добиться реализации наследования классов Admin и User
от BaseUser так, чтобы модели обоих классов сохранялись в одну таблицу.
По крайне мере в текущих версиях SQLModel и Pydantic все способы упираются в ошибку
ValueError: <class 'sqlalchemy.orm.base.Mapped'> has no matching SQLAlchemy type

Поэтому добавляются классы MLUser MLAdmin, которые не являются потомками SQLModel, но реализуют функциональность модели.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional
from models.user import User, UserAuth, UserRole


class BaseMLUser:
    def __init__(self, user: User):
        self._user: User = user

    @property
    def user(self) -> User:
        return self._user

    @user.setter
    def user(self, user: User):
        self._user = user

    @property
    def user_id(self) -> Optional[int]:
        return self._user.id if self._user.id else None

    @property
    def auth(self) -> Optional[UserAuth]:
        return self._user.auth if self._user.auth else None

    @property
    def name(self) -> Optional[str]:
        return self._user.name if self._user.name else None

    @name.setter
    def name(self, name: str):
        self._user.name = name

    @property
    def email(self) -> Optional[str]:
        return self._user.email if self._user.email else None

    @email.setter
    def email(self, email: str):
        self._user.email = email

    @property
    def created(self) -> datetime:
        return self._user.created

    def __str__(self):
        return f"{self._user.role}(id={self._user.id} name:'{self._user.name}' email:{self._user.email} login:{self._user.auth.login if self._user.auth else None})"


class MLUser(BaseMLUser):
    def __init__(self, user: User = None, **kwargs):
        user = user if user else User(role=UserRole.USER, **kwargs)
        user.balance = user.balance if user.balance else Decimal("0.0")
        super().__init__(user)

    @property
    def balance(self) -> Decimal:
        return self._user.balance

    @balance.setter
    def balance(self, balance: Decimal):
        self._user.balance = balance


class MLAdmin(BaseMLUser):
    def __init__(self, user: User = None, **kwargs):
        user = user if user else User(role=UserRole.ADMIN, **kwargs)
        super().__init__(user)
