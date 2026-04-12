from typing import Iterable, Sequence, Optional
from sqlmodel import Session, select
from models.ml_model import MLModel


def get_ml_model_by_id(ml_model_id: int, session: Session) -> MLModel:
    try:
        stmt = select(MLModel).where(MLModel.id == ml_model_id)
        ml_model = session.exec(stmt).first()
        if not ml_model or not isinstance(ml_model, MLModel):
            raise ValueError(f"Invalid ML model by id={ml_model_id}")
        return ml_model
    except Exception:
        raise

def add_ml_model(ml_model: MLModel, session: Session) -> MLModel:
    try:
        session.add(ml_model)
        session.commit()
        session.refresh(ml_model)
        return ml_model
    except Exception:
        session.rollback()
        raise

def add_ml_models(ml_models: Iterable[MLModel], session: Session) -> Iterable[MLModel]:
    try:
        session.add_all([ml_model for ml_model in ml_models])
        session.commit()
        for ml_model in ml_models:
            session.refresh(ml_model)
        return ml_models
    except Exception:
        session.rollback()
        raise

def delete_ml_model(ml_model: MLModel, session: Session):
    try:
        session.delete(ml_model)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_ml_models(ml_models: Iterable[MLModel], session: Session):
    try:
        for ml_model in ml_models:
            session.delete(ml_model)
        session.commit()
    except Exception:
        session.rollback()
        raise

def get_all_ml_models(session: Session) -> Sequence[MLModel]:
    try:
        stmt = select(MLModel)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_ml_model_by_reference(ml_model_reference: str, session: Session) -> Optional[MLModel]:
    try:
        stmt = select(MLModel).where(MLModel.reference == ml_model_reference)
        ml_model = session.exec(stmt).first()
        if ml_model and isinstance(ml_model, MLModel):
            return ml_model
        return None
    except Exception:
        raise