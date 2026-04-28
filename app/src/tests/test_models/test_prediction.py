import pytest
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import ValidationError

from models.ml_model import MLModel
from models.ml_task import MLTask
from models.prediction import Prediction
from models.user import User


def create_test_ml_task() -> MLTask:
    user = User(id=1, name="test", email="test@example.com")
    ml_model = MLModel(id=1, reference="test", description="description")
    return MLTask(user=user, ml_model=ml_model)

def test_valid_prediction_minimal():
    prediction = Prediction(ml_task=create_test_ml_task())
    assert isinstance(prediction, Prediction)
    assert prediction.id is None
    assert prediction.result is None
    assert prediction.cost == Decimal("0.0")
    assert isinstance(prediction.created, datetime)
    assert prediction.created.tzinfo == timezone.utc

def test_result_invalid_type():
    prediction = Prediction(ml_task=create_test_ml_task(), result=123)
    with pytest.raises(ValidationError) as exc_info:
        Prediction.model_validate(prediction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('result',)

def test_cost_invalid_type():
    prediction = Prediction(ml_task=create_test_ml_task(), cost="invalid_cost")
    with pytest.raises(ValidationError) as exc_info:
        Prediction.model_validate(prediction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_parsing'
    assert errors[0]['loc'] == ('cost',)

def test_cost_too_many_digits():
    invalid_cost = Decimal("12345678.12345")
    prediction = Prediction(ml_task=create_test_ml_task(), cost=invalid_cost)
    with pytest.raises(ValidationError) as exc_info:
        Prediction.model_validate(prediction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_max_digits'
    assert errors[0]['loc'] == ('cost',)

def test_cost_negative():
    invalid_cost = Decimal("-1")
    prediction = Prediction(ml_task=create_test_ml_task(), cost=invalid_cost)
    with pytest.raises(ValidationError) as exc_info:
        Prediction.model_validate(prediction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'greater_than_equal'
    assert errors[0]['loc'] == ('cost',)

def test_ml_task_invalid():
    model = MLModel(name="not ml task")
    with pytest.raises(KeyError):
        Prediction(ml_task=model)
    with pytest.raises(AttributeError):
        Prediction(ml_task="not ml task")