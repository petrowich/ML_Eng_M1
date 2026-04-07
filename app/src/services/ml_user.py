"""
В этом модуле сервис для класса-обёртки MLUser модели User

Из-за проблемы наследования моделей SQLModel не удалось добиться реализации наследования классов Admin и User
от BaseUser так, чтобы модели обоих классов сохранялись в одну таблицу.
По крайне мере в текущих версиях SQLModel и Pydantic все способы упираются в ошибку
ValueError: <class 'sqlalchemy.orm.base.Mapped'> has no matching SQLAlchemy type
"""
from typing import Iterable, Optional, Sequence
from sqlmodel import Session, select
from models.user import UserRole, User, UserAuth
from models.ml_user import MLUser


def create_user(user: MLUser, session: Session) -> MLUser:
    try:
        session.add(user.user)
        session.commit()
        session.refresh(user.user)
        return user
    except Exception:
        raise

def create_users(users: Iterable[MLUser], session: Session) -> Iterable[MLUser]:
    try:
        session.add_all([user.user for user in users])
        session.commit()
        for user in users:
            session.refresh(user.user)
        return users
    except Exception:
        session.rollback()
        raise

def get_all_users(session: Session) -> Sequence[MLUser]:
    try:
        stmt = select(User).where(User.role == UserRole.USER)
        users = session.exec(stmt).all()
        return [MLUser(user) for user in users]
    except Exception:
        raise

def get_user_by_email(email, session: Session) -> Optional[MLUser]:
    try:
        stmt = select(User).where(User.role == UserRole.USER).where(User.email == email)
        user = session.exec(stmt).first()
        return MLUser(user) if user else None
    except Exception:
        raise

def get_ml_user_by_login(login, session: Session) -> Optional[MLUser]:
    try:
        stmt = select(User).join(UserAuth).where(User.role == UserRole.USER).where(UserAuth.login == login)
        user = session.exec(stmt).first()
        return MLUser(user) if user else None
    except Exception:
        raise
