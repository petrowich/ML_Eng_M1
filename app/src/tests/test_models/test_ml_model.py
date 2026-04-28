import pytest
from decimal import Decimal
from pydantic import ValidationError
from models.ml_model import MLModel

def test_valid_ml_model_minimal():
    ml_model = MLModel(reference="test", description="description")
    assert isinstance(ml_model, MLModel)
    assert ml_model.reference == "test"
    assert ml_model.description == "description"
    assert ml_model.prediction_cost == Decimal("0.0")
    assert ml_model.name is None
    assert ml_model.id is None
    assert ml_model.ml_tasks == []

def test_missing_reference():
    ml_model = MLModel(name="Test")
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('reference',)

def test_reference_empty_string():
    ml_model = MLModel(name="Test", reference="")
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_short'
    assert errors[0]['loc'] == ('reference',)

def test_reference_too_long():
    long_ref = "a" * 51
    ml_model = MLModel(name="Test", reference=long_ref)
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('reference',)

def test_missing_name():
    ml_model = MLModel(reference="Test")
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('name',)

def test_name_too_long():
    long_name = "a" * 256
    ml_model = MLModel(reference="Test", name=long_name)
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('name',)

def test_description_too_long():
    long_desc = "a" * 2001
    ml_model = MLModel(name="Test", reference="Test", description=long_desc)
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('description',)

def test_prediction_cost_invalid_type():
    ml_model = MLModel(name="Test", reference="Test", prediction_cost="invalid_cost")
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_parsing'
    assert errors[0]['loc'] == ('prediction_cost',)

def test_prediction_cost_too_many_digits():
    invalid_cost = Decimal("12345678.12345")
    ml_model = MLModel(name="Test", reference="Test", prediction_cost=invalid_cost)
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_max_digits'
    assert errors[0]['loc'] == ('prediction_cost',)

def test_prediction_cost_negative():
    invalid_cost = Decimal("-1")
    ml_model = MLModel(name="Test", reference="Test", prediction_cost=invalid_cost)
    with pytest.raises(ValidationError) as exc_info:
        MLModel.model_validate(ml_model)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'greater_than_equal'
    assert errors[0]['loc'] == ('prediction_cost',)