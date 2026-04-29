from typing import Iterable, Optional, Sequence
from sqlalchemy import Row
from sqlmodel import Session, select

from models.ml_task import MLTask
from models.transaction import Transaction
from models.user import User, UserAuth


def get_user_by_id(user_id: int, session: Session) -> User:
    try:
        stmt = select(User).where(User.id == user_id)
        user = session.exec(stmt).first()
        if not user or not isinstance(user, User):
            raise ValueError(f"Invalid user by id={user_id}")
        return user
    except Exception:
        raise

def add_user(user: User, session: Session) -> User:
    try:
        session.add(user)
        session.flush()
        session.refresh(user)
        return user
    except Exception:
        session.rollback()
        raise

def add_users(users: Iterable[User], session: Session) -> Iterable[User]:
    try:
        session.add_all([user for user in users])
        session.flush()
        for user in users:
            session.refresh(user)
        return users
    except Exception:
        session.rollback()
        raise

def delete_user(user: User, session: Session):
    try:
        session.delete(user)
        session.flush()
    except Exception:
        session.rollback()
        raise

def delete_users(users: Iterable[User], session: Session):
    try:
        for user in users:
            session.delete(user)
            session.flush()
    except Exception:
        session.rollback()
        raise

def get_all_users(session: Session) -> Sequence[User]:
    try:
        stmt = select(User)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_user_by_email(email, session: Session) -> Optional[User]:
    try:
        stmt = select(User).where(User.email == email)
        user = session.exec(stmt).first()
        if isinstance(user, Row):
            user = user[0]
        return user
    except Exception:
        raise

def get_user_by_login(login, session: Session) -> Optional[User]:
    try:
        stmt = select(User).join(UserAuth).where(UserAuth.login == login)
        user = session.exec(stmt).first()
        if isinstance(user, Row):
            user = user[0]
        return user
    except Exception:
        session.rollback()
        raise

def update_password_hash(auth: UserAuth, session: Session):
    try:
        session.add(auth)
        session.flush()
    except Exception:
        session.rollback()
        raise

def get_user_auth_by_login(login, session: Session) -> Optional[UserAuth]:
    try:
        stmt = select(UserAuth).where(UserAuth.login == login)
        user_auth = session.exec(stmt).first()
        if not user_auth or not isinstance(user_auth, UserAuth):
            raise ValueError(f"Invalid user auth by login={login}")
        return user_auth
    except Exception:
        session.rollback()
        raise

def get_user_auth_by_email(email, session: Session) -> Optional[UserAuth]:
    try:
        stmt = select(UserAuth).join(User).where(User.email == email)
        user_auth = session.exec(stmt).first()
        if not user_auth or not isinstance(user_auth, UserAuth):
            raise ValueError(f"Invalid user auth by login={email}")
        return user_auth
    except Exception:
        session.rollback()
        raise

def get_user_by_ml_task(ml_task: MLTask, session: Session) -> Optional[User]:
    try:
        if ml_task.ml_model_id is not None:
            stmt = select(User).where(User.id == ml_task.user_id)
            ml_model = session.exec(stmt).first()
            if ml_model and isinstance(ml_model, User):
                return ml_model
        return None
    except Exception:
        raise

def get_user_by_ml_transaction(transaction: Transaction, session: Session) -> Optional[User]:
    try:
        if transaction.user_id is not None:
            stmt = select(User).where(User.id == transaction.user_id)
            ml_model = session.exec(stmt).first()
            if ml_model and isinstance(ml_model, User):
                return ml_model
        return None
    except Exception:
        raise