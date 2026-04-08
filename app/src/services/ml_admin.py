"""
В этом модуле сервис для класса-обёртки MLAdmin модели User

Из-за проблемы наследования моделей SQLModel не удалось добиться реализации наследования классов Admin и User
от BaseUser так, чтобы модели обоих классов сохранялись в одну таблицу.
По крайне мере в текущих версиях SQLModel и Pydantic все способы упираются в ошибку
ValueError: <class 'sqlalchemy.orm.base.Mapped'> has no matching SQLAlchemy type
"""
from typing import Iterable, Optional, Sequence
from sqlmodel import Session, select
from models.user import UserRole, User, UserAuth
from models.ml_user import MLAdmin


def create_admin(admin: MLAdmin, session: Session) -> MLAdmin:    
    try:
        session.add(admin.user)
        session.commit()
        session.refresh(admin.user)
        return admin
    except Exception:
        session.rollback()
        raise

def create_admins(admins: Iterable[MLAdmin], session: Session) -> Iterable[MLAdmin]:
    try:
        session.add_all([user.user for user in admins])
        session.commit()
        for user in admins:
            session.refresh(user.user)
        return admins
    except Exception:
        session.rollback()
        raise
    
def update_admin(admin: MLAdmin, session: Session):
    try:
        session.add(admin.user)
        session.commit()
    except Exception:
        session.rollback()
        raise

def update_admins(admins: Iterable[MLAdmin], session: Session):
    try:
        session.add_all([user.user for user in admins])
        session.commit()
    except Exception:
        session.rollback()
        raise   
    
def delete_admin(admin: MLAdmin, session: Session):
    try:
        session.delete(admin.user)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_admins(admins: Iterable[MLAdmin], session: Session):
    try:
        for admin in admins:
            session.delete(admin.user)
        session.commit()
    except Exception:
        session.rollback()
        raise     

def get_all_admins(session: Session) -> Sequence[MLAdmin]:
    try:
        stmt = select(User).where(User.role == UserRole.ADMIN)
        users = session.exec(stmt).all()
        return [MLAdmin(user) for user in users]
    except Exception:
        raise

def get_admin_by_email(email, session: Session) -> Optional[MLAdmin]:
    try:
        stmt = select(User).where(User.role == UserRole.ADMIN).where(User.email == email)
        user = session.exec(stmt).first()
        return MLAdmin(user) if user else None
    except Exception:
        raise

def get_ml_user_by_login(login, session: Session) -> Optional[MLAdmin]:
    try:
        stmt = select(User).join(UserAuth).where(User.role == UserRole.USER).where(UserAuth.login == login)
        user = session.exec(stmt).first()
        return MLAdmin(user) if user else None
    except Exception:
        raise
