from typing import Iterable, Sequence
from sqlmodel import Session, select
from models.ml_model import MLModel


def get_ml_model_by_id(ml_model_id: int, session: Session) -> MLModel:
    try:
        stmt = select(MLModel).where(MLModel.id == ml_model_id)
        ml_model = session.exec(stmt).first()
        if not ml_model and not isinstance(ml_model, MLModel):
            raise ValueError(f"Invalid ML model by id={ml_model}")
        return ml_model
    except Exception:
        raise

def create_ml_model(ml_model: MLModel, session: Session) -> MLModel:
    try:
        session.add(ml_model)
        session.commit()
        session.refresh(ml_model)
        return ml_model
    except Exception:
        session.rollback()
        raise

def create_ml_models(ml_models: Iterable[MLModel], session: Session) -> Iterable[MLModel]:
    try:
        session.add_all([ml_model for ml_model in ml_models])
        session.commit()
        for ml_model in ml_models:
            session.refresh(ml_model)
        return ml_models
    except Exception:
        session.rollback()
        raise
        
def update_ml_model(ml_model: MLModel, session: Session):
    try:
        session.add(ml_model)
        session.commit()
    except Exception:
        session.rollback()
        raise    
    
def update_ml_models(ml_models: Iterable[MLModel], session: Session):
    try:
        session.add_all([ml_model for ml_model in ml_models])
        session.commit()
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
