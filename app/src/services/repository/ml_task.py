import json
import logging
import uuid
from typing import Iterable, Sequence
from sqlmodel import Session, select
from models.ml_task import MLTask
from models.user import User
from pika import BasicProperties
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from pika.adapters.blocking_connection import BlockingChannel


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def get_ml_task_by_id(ml_task_id: int, session: Session) -> MLTask:
    try:
        stmt = select(MLTask).where(MLTask.id == ml_task_id)
        ml_task = session.exec(stmt).first()
        if not ml_task or not isinstance(ml_task, MLTask):
            raise ValueError(f"Invalid ML task by id={ml_task_id}")
        return ml_task
    except Exception:
        raise

def add_ml_task(ml_task: MLTask, session: Session) -> MLTask:
    try:
        session.add(ml_task)
        session.commit()
        session.refresh(ml_task)
        return ml_task
    except Exception:
        session.rollback()
        raise

def add_ml_tasks(ml_tasks: Iterable[MLTask], session: Session) -> Iterable[MLTask]:
    try:
        session.add_all([ml_task for ml_task in ml_tasks])
        session.commit()
        for ml_task in ml_tasks:
            session.refresh(ml_task)
        return ml_tasks
    except Exception:
        session.rollback()
        raise        

def delete_ml_task(ml_task: MLTask, session: Session):
    try:
        session.delete(ml_task)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_ml_tasks(ml_tasks: Iterable[MLTask], session: Session):
    try:
        for ml_task in ml_tasks:
            session.delete(ml_task)
        session.commit()
    except Exception:
        session.rollback()
        raise

def get_all_ml_tasks(session: Session) -> Sequence[MLTask]:
    try:
        stmt = select(MLTask)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_ml_tasks_by_user(user: User, session: Session) -> Sequence[MLTask]:
    try:
        stmt = select(MLTask).join(User).where(User.id == user.id)
        return session.exec(stmt).all()
    except Exception:
        raise
