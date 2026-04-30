from decimal import Decimal
import services.repository.user
import services.repository.ml_model
import services.repository.ml_task
from models.ml_model import MLModel
from models.user import User, UserAuth

def test_ml_models_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/ml_models/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

class FakeBlockingChannel:
    def basic_publish(self, *args, **kwargs):
        return None

def test_submit_task_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    from datasource.rabbitmq import get_channel
    app.dependency_overrides[get_channel] = lambda: FakeBlockingChannel()
    resp = client.post(
        "/ml_models/submit_task",
        data={"model": "any", "text": "request"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_submit_task_authorized_success_redirects_303_and_sets_task_queued(client, app, session):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    from datasource.rabbitmq import get_channel
    app.dependency_overrides[get_channel] = lambda: FakeBlockingChannel()
    user = User(email="user@example.test", name="User", balance=Decimal("100.00"), auth=UserAuth(login="test_login", pwd_hash="hash"))
    ml_model = MLModel(name="model", reference="model", prediction_cost=Decimal("5.00"))
    services.repository.user.add_user(user, session)
    services.repository.ml_model.add_ml_model(ml_model, session)
    session.commit()
    session.refresh(user)
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.post(
        "/ml_models/submit_task",
        data={"model": "model", "text": "request"},
        follow_redirects=False,
    )
    ml_tasks = services.repository.ml_task.get_ml_tasks_by_user(user, session)
    print(ml_tasks)
    assert resp.status_code == 200
    assert len(ml_tasks) == 1
