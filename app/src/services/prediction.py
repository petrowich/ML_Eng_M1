from typing import Iterable, Sequence
from sqlmodel import Session, select
from models.ml_task import MLTask
from models.prediction import Prediction
from models.user import User


def get_prediction_by_id(prediction_id: int, session: Session) -> Prediction:
    try:
        stmt = select(Prediction).where(Prediction.id == prediction_id)
        prediction = session.exec(stmt).first()
        if not prediction or not isinstance(prediction, Prediction):
            raise ValueError(f"Invalid prediction by id={prediction_id}")
        return prediction
    except Exception:
        raise

def add_prediction(prediction: Prediction, session: Session) -> Prediction:
    try:
        session.add(prediction)
        session.commit()
        session.refresh(prediction)
        return prediction
    except Exception:
        session.rollback()
        raise

def add_predictions(predictions: Iterable[Prediction], session: Session) -> Iterable[Prediction]:
    try:
        session.add_all([prediction for prediction in predictions])
        session.commit()
        for prediction in predictions:
            session.refresh(prediction)
        return predictions
    except Exception:
        session.rollback()
        raise

def delete_prediction(prediction: Prediction, session: Session):
    try:
        session.delete(prediction)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_predictions(predictions: Iterable[Prediction], session: Session):
    try:
        for prediction in predictions:
            session.delete(prediction)
        session.commit()
    except Exception:
        session.rollback()
        raise

def get_all_predictions(session: Session) -> Sequence[Prediction]:
    try:
        stmt = select(Prediction)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_predictions_by_user(user: User, session: Session) -> Sequence[Prediction]:
    try:
        stmt = select(Prediction).join(MLTask).join(User).where(User.id == user.id)
        return session.exec(stmt).all()
    except Exception:
        raise