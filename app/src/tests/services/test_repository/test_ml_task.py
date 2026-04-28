from decimal import Decimal

import pytest
from sqlmodel import Session
from models.ml_model import MLModel
from models.ml_task import MLTask, MLTaskStatus
from models.user import User
from services.repository.ml_task import (
    get_ml_task_by_id,
    add_ml_task,
    add_ml_tasks,
    delete_ml_task,
    delete_ml_tasks,
    get_all_ml_tasks,
    get_ml_tasks_by_user,
)

def create_test_user(session: Session, user_name="test user", user_email="email") -> User:
    user = User(name=user_name, email=user_email)
    session.add(user)
    return user

def create_test_ml_model(session: Session, model_ref="MODEL_TEST", model_name="test model") -> MLModel:
    ml_model = MLModel(reference=model_ref, name=model_name)
    session.add(ml_model)
    return ml_model

def test_get_ml_task_by_id(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task = MLTask(user=user, ml_model=ml_model)
    added_task = add_ml_task(ml_task, session)
    assert isinstance(added_task, MLTask)
    assert added_task.id is not None
    assert added_task.status == MLTaskStatus.NEW
    assert added_task.ml_model.reference == "MODEL_TEST"
    assert added_task.duration_ms == Decimal('0.0')

def test_get_ml_task_by_id_not_found(session: Session):
    with pytest.raises(ValueError):
        get_ml_task_by_id(999, session)

def test_add_ml_task(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task = MLTask(user=user, ml_model=ml_model)
    added_task = add_ml_task(ml_task, session)
    retrieved = get_ml_task_by_id(added_task.id, session)
    assert isinstance(retrieved, MLTask)
    assert retrieved.id == added_task.id
    assert retrieved.ml_model.reference == "MODEL_TEST"

def test_add_ml_tasks(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user, ml_model=ml_model)
    ml_task_02 = MLTask(user=user, ml_model=ml_model)
    tasks = [ml_task_01, ml_task_02]
    added_tasks = add_ml_tasks(tasks, session)
    assert len(added_tasks) == 2
    assert all(task.id is not None for task in added_tasks)
    all_tasks = get_all_ml_tasks(session)
    assert len(all_tasks) == 2

def test_delete_ml_task(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user, ml_model=ml_model)
    ml_task_02 = MLTask(user=user, ml_model=ml_model)
    tasks = [ml_task_01, ml_task_02]
    add_ml_tasks(tasks, session)
    delete_ml_task(ml_task_01, session)
    with pytest.raises(ValueError):
        get_ml_task_by_id(ml_task_01.id, session)

def test_delete_ml_tasks(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user, ml_model=ml_model)
    ml_task_02 = MLTask(user=user, ml_model=ml_model)
    tasks = [ml_task_01, ml_task_02]
    add_ml_tasks(tasks, session)
    delete_ml_tasks(tasks, session)
    all_tasks = get_all_ml_tasks(session)
    assert len(all_tasks) == 0

def test_get_all_ml_tasks(session: Session):
    user = create_test_user(session, "test user", "test@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user, ml_model=ml_model)
    ml_task_02 = MLTask(user=user, ml_model=ml_model)
    tasks = [ml_task_01, ml_task_02]
    add_ml_tasks(tasks, session)
    all_tasks = get_all_ml_tasks(session)
    assert len(all_tasks) == 2
    assert all(isinstance(ml_task, MLTask) for ml_task in all_tasks)

def test_get_ml_tasks_by_user(session: Session):
    user01 = create_test_user(session, "test user 1", "test1@t.t")
    user02 = create_test_user(session, "test user 2", "test2@t.t")
    ml_model = create_test_ml_model(session, "MODEL_TEST", "test model")
    ml_task_01 = MLTask(user=user01, ml_model=ml_model)
    ml_task_02 = MLTask(user=user01, ml_model=ml_model)
    ml_task_03 = MLTask(user=user02, ml_model=ml_model)
    tasks = [ml_task_01, ml_task_02, ml_task_03]
    add_ml_tasks(tasks, session)
    retrieved = get_ml_tasks_by_user(user01, session)
    assert len(retrieved) == 2
    assert all(isinstance(ml_task, MLTask) for ml_task in retrieved)
    assert any(ml_task.ml_model.reference == "MODEL_TEST" for ml_task in retrieved)
