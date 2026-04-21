from typing import Iterable, Optional, Sequence
from sqlmodel import Session, select
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
        session.commit()
        session.refresh(user)
        return user
    except Exception:
        session.rollback()
        raise

def add_users(users: Iterable[User], session: Session) -> Iterable[User]:
    try:
        session.add_all([user for user in users])
        session.commit()
        for user in users:
            session.refresh(user)
        return users
    except Exception:
        session.rollback()
        raise

def delete_user(user: User, session: Session):
    try:
        session.delete(user)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_users(users: Iterable[User], session: Session):
    try:
        for user in users:
            session.delete(user)
        session.commit()
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
        return user
    except Exception:
        raise

def get_user_by_login(login, session: Session) -> Optional[User]:
    try:
        stmt = select(User).join(UserAuth).where(UserAuth.login == login)
        user = session.exec(stmt).first()
        return user
    except Exception:
        session.rollback()
        raise

def update_password_hash(auth: UserAuth, session: Session):
    try:
        session.add(auth)
        session.commit()
    except Exception:
        session.rollback()
        raise
