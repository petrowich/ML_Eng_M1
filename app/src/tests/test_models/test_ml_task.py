import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.ml_model import MLModel
from models.ml_task import MLTask, MLTaskStatus
from models.user import User


def create_test_user() -> User:
    return User(id=1, name="test", email="test@example.com")

def create_test_ml_model() -> MLModel:
    return MLModel(id=2, reference="test", description="description")

def test_valid_ml_task_minimal():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model())
    assert isinstance(ml_task, MLTask)
    assert ml_task.user.id == 1
    assert ml_task.ml_model.id == 2
    assert ml_task.id is None
    assert ml_task.prediction is None
    assert ml_task.transaction_id is None
    assert ml_task.transaction is None
    assert ml_task.request is None
    assert ml_task.status == MLTaskStatus.NEW
    assert ml_task.duration_ms == 0
    assert ml_task.failure is None
    assert isinstance(ml_task.timestamp, datetime)
    assert ml_task.timestamp.tzinfo == timezone.utc

def test_status_invalid():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model(), status="INVALID")
    with pytest.raises(ValidationError) as exc_info:
        MLTask.model_validate(ml_task)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'enum'
    assert errors[0]['loc'] == ('status',)

def test_duration_ms_invalid_type():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model(), duration_ms="zero")
    with pytest.raises(ValidationError) as exc_info:
        MLTask.model_validate(ml_task)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'int_parsing'
    assert errors[0]['loc'] == ('duration_ms',)

def test_transaction_id_invalid():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model(), transaction_id="not-a-uuid")
    with pytest.raises(ValidationError) as exc_info:
        MLTask.model_validate(ml_task)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'uuid_parsing'
    assert errors[0]['loc'] == ('transaction_id',)

def test_request_invalid_type():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model(), request=123)
    with pytest.raises(ValidationError) as exc_info:
        MLTask.model_validate(ml_task)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('request',)

def test_failure_invalid_type():
    ml_task = MLTask(user=create_test_user(), ml_model=create_test_ml_model(), failure=123)
    with pytest.raises(ValidationError) as exc_info:
        MLTask.model_validate(ml_task)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('failure',)

def test_user_invalid():
    model = MLModel(name="not user", reference="task")
    with pytest.raises(ValueError):
         MLTask(user=model, ml_model=model)
    with pytest.raises(AttributeError):
        MLTask(user="not user", ml_model=model)

def test_ml_model_invalid():
    user = User(name="not ml model")
    with pytest.raises(ValueError):
         MLTask(user=user, ml_model=user)
    with pytest.raises(AttributeError):
        MLTask(user=user, ml_model="not ml user")