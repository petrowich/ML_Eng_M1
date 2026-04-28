import pytest
from decimal import Decimal
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from models.ml_model import MLModel
from services.repository.ml_model import (
    get_ml_model_by_id,
    add_ml_model,
    add_ml_models,
    delete_ml_model,
    delete_ml_models,
    get_all_ml_models,
    get_ml_model_by_reference,
)

def test_get_ml_model_by_id(session: Session):
    ml_model = MLModel(reference="MODEL", name="model", description="desc", prediction_cost=Decimal('1.5'))
    added_model = add_ml_model(ml_model, session)
    retrieved = get_ml_model_by_id(added_model.id, session)
    assert isinstance(retrieved, MLModel)
    assert retrieved.id == added_model.id
    assert retrieved.reference == "MODEL"
    assert retrieved.name == "model"
    assert retrieved.description == "desc"
    assert retrieved.prediction_cost == Decimal('1.5')

def test_get_ml_model_by_id_not_found(session: Session):
    with pytest.raises(ValueError):
        get_ml_model_by_id(999, session)

def test_add_ml_model(session: Session):
    ml_model = MLModel(reference="NEW_MODEL", description="new desc", name="New Model", prediction_cost=Decimal('99.99'))
    added_model = add_ml_model(ml_model, session)
    assert added_model.id is not None
    retrieved = get_ml_model_by_id(added_model.id, session)
    assert retrieved.reference == "NEW_MODEL"
    assert retrieved.description == "new desc"
    assert retrieved.name == "New Model"
    assert retrieved.prediction_cost == Decimal('99.99')

def test_reference_field_constraints(session: Session):
    invalid_model = MLModel(reference=None)
    with pytest.raises(IntegrityError):
        add_ml_model(invalid_model, session)

    add_ml_model(MLModel(reference='test', name="model"), session)
    duplicate_model = MLModel(reference='test', name="duplicate model")
    with pytest.raises(IntegrityError):
        add_ml_model(duplicate_model, session)

def test_add_ml_models(session: Session):
    models = [MLModel(reference="test01", name="model 1"),
              MLModel(reference="test02", name="model 2")]
    added_models = add_ml_models(models, session)
    assert len(added_models) == 2
    assert all(model.id is not None for model in added_models)

    all_models = get_all_ml_models(session)
    assert len(all_models) == 2

def test_add_ml_models_with_duplicates(session: Session):
    models = [MLModel(reference="test", name="model"),
              MLModel(reference="test", name="duplicate model")]
    with pytest.raises(IntegrityError):
        add_ml_models(models, session)

def test_delete_ml_model(session: Session):
    model_1 = MLModel(reference="test01", name="model 1")
    model_2 = MLModel(reference="test02", name="model 2")
    models = [model_1, model_2]
    add_ml_models(models, session)
    delete_ml_model(model_1, session)
    all_models = get_all_ml_models(session)
    assert len(all_models) == 1
    with pytest.raises(ValueError):
        get_ml_model_by_id(model_1.id, session)

def test_delete_ml_models(session: Session):
    models = [MLModel(reference="test01", name="model 1"),
              MLModel(reference="test02", name="model 2")]
    add_ml_models(models, session)
    delete_ml_models(models, session)
    all_models = get_all_ml_models(session)
    assert len(all_models) == 0

def test_get_all_ml_models(session: Session):
    models = [MLModel(reference="test01", name="model 1"),
              MLModel(reference="test02", name="model 2")]
    add_ml_models(models, session)
    all_models = get_all_ml_models(session)
    assert len(all_models) == 2
    assert all(isinstance(model, MLModel) for model in all_models)

def test_get_ml_model_by_reference(session: Session):
    add_ml_model(MLModel(reference="test01", name="model") , session)
    add_ml_model(MLModel(reference="required", name="required model") , session)
    retrieved = get_ml_model_by_reference("required", session)
    assert retrieved is not None
    assert isinstance(retrieved, MLModel)
    assert retrieved.reference == "required"
