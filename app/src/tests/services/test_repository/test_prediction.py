from decimal import Decimal

import pytest
from sqlmodel import Session
from models.ml_model import MLModel
from models.ml_task import MLTask
from models.prediction import Prediction
from models.user import User
from services.repository.prediction import add_prediction, get_prediction_by_id, add_predictions, get_all_predictions, \
    delete_prediction, delete_predictions, get_predictions_by_user


def create_test_user(session: Session, user_name="test user", user_email="email") -> User:
    user = User(name=user_name, email=user_email)
    session.add(user)
    return user

def create_test_ml_model(session: Session, model_ref="MODEL_TEST", model_name="test model") -> MLModel:
    ml_model = MLModel(reference=model_ref, name=model_name)
    session.add(ml_model)
    return ml_model

def create_test_ml_task(session: Session, user_name="test user", user_email="email", model_ref="MODEL_TEST", model_name="test model") -> MLTask:
    user = create_test_user(session, user_name, user_email)
    ml_model = create_test_ml_model(session, model_ref, model_name)
    ml_task = MLTask(user=user, ml_model=ml_model)
    session.add(ml_task)
    return ml_task

def test_get_prediction_by_id(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction = Prediction(ml_task=ml_task)
    added_prediction = add_prediction(prediction, session)
    assert isinstance(added_prediction, Prediction)
    assert added_prediction.ml_task.ml_model.reference == "MODEL_TEST"
    assert added_prediction.cost == Decimal('0.0')

def test_get_prediction_by_id_not_found(session: Session):
    with pytest.raises(ValueError):
        get_prediction_by_id(999, session)

def test_add_prediction(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction = Prediction(ml_task=ml_task)
    added_prediction = add_prediction(prediction, session)
    retrieved = get_prediction_by_id(added_prediction.id, session)
    assert isinstance(retrieved, Prediction)
    assert retrieved.id == added_prediction.id
    assert retrieved.ml_task.ml_model.reference == "MODEL_TEST"

def test_add_predictions(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction_01 = Prediction(ml_task=ml_task)
    prediction_02 = Prediction(ml_task=ml_task)
    predictions = [prediction_01, prediction_02]
    added_predictions = add_predictions(predictions, session)
    assert len(added_predictions) == 2
    assert all(prediction.id is not None for prediction in added_predictions)
    all_tasks = get_all_predictions(session)
    assert len(all_tasks) == 2

def test_delete_prediction(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction_01 = Prediction(ml_task=ml_task)
    prediction_02 = Prediction(ml_task=ml_task)
    predictions = [prediction_01, prediction_02]
    add_predictions(predictions, session)
    delete_prediction(prediction_01, session)
    with pytest.raises(ValueError):
        get_prediction_by_id(prediction_01.id, session)

def test_delete_predictions(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction_01 = Prediction(ml_task=ml_task)
    prediction_02 = Prediction(ml_task=ml_task)
    predictions = [prediction_01, prediction_02]
    add_predictions(predictions, session)
    delete_predictions(predictions, session)
    all_tasks = get_all_predictions(session)
    assert len(all_tasks) == 0

def test_get_all_predictions(session: Session):
    ml_task = create_test_ml_task(session, "test user", "test@t.t", "MODEL_TEST", "test model")
    prediction_01 = Prediction(ml_task=ml_task)
    prediction_02 = Prediction(ml_task=ml_task)
    tasks = [prediction_01, prediction_02]
    add_predictions(tasks, session)
    all_predictions = get_all_predictions(session)
    assert len(all_predictions) == 2
    assert all(isinstance(prediction, Prediction) for prediction in all_predictions)
    assert all(prediction.ml_task.ml_model.reference=="MODEL_TEST" for prediction in all_predictions)

def test_get_predictions_by_user(session: Session):
    user01 = create_test_user(session, "test user 1", "test1@t.t")
    user02 = create_test_user(session, "test user 2", "test2@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user01, ml_model=ml_model)
    ml_task_02 = MLTask(user=user01, ml_model=ml_model)
    ml_task_03 = MLTask(user=user02, ml_model=ml_model)
    prediction_01 = Prediction(ml_task=ml_task_01)
    prediction_02 = Prediction(ml_task=ml_task_02)
    prediction_03 = Prediction(ml_task=ml_task_03)
    predictions = [prediction_01, prediction_02, prediction_03]
    add_predictions(predictions, session)
    retrieved = get_predictions_by_user(user01, session)
    assert len(retrieved) == 2
    assert all(isinstance(prediction, Prediction) for prediction in retrieved)
    assert any(prediction.ml_task.ml_model.reference == "MODEL_TEST" for prediction in retrieved)