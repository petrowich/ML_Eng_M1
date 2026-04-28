import importlib
import os
import sys
import types
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlmodel import SQLModel, Session

@pytest.fixture(scope="session", autouse=True)
def set_project_cwd():
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)

@pytest.fixture(scope="session")
def app():

    import datasource.config as config_module

    settings_stub = types.SimpleNamespace(
        APP_NAME="test-app",
        APP_DESCRIPTION="test",
        APP_PORT=8080,
        LOG_LEVEL="INFO",

        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test",
        ENGINE_ECHO_DEBUG=False,

        RABBITMQ_HOST="localhost",
        RABBITMQ_PORT=5672,
        RABBITMQ_USER="guest",
        RABBITMQ_PASSWORD="guest",
        RABBITMQ_HEARTBEAT=60,
        RABBITMQ_BLOCKED_CONNECTION_TIMEOUT=300,

        QUEUE_ML_TASKS="test-ml-tasks",
        QUEUE_PREDICTIONS="test-predictions",

        COOKIE_NAME="ML_SERVICE",
        SECRET_KEY="test-secret-key",

        auth_token_cookie_name=lambda: "ML_SERVICE_AUTH_TOKEN",
        log_level=20,
    )
    config_module.get_settings = lambda: settings_stub

    fake_prediction_module = types.ModuleType("consumers.prediction")
    fake_prediction_module.prediction_consumer = types.SimpleNamespace(
        start=lambda: None,
        stop=lambda: None,
    )
    sys.modules["consumers.prediction"] = fake_prediction_module

    sys.modules.pop("api", None)
    api = importlib.import_module("api")

    api.init_db = lambda drop_all=False: None
    api.declare_queue = lambda *args, **kwargs: None
    api.get_queue_ml_tasks = lambda: "dummy-queue"

    return api.app

@pytest.fixture(scope="session")
def engine():
   engine = create_engine(
       "sqlite:///:memory:",
       connect_args={"check_same_thread": False},
       poolclass=StaticPool,
   )
   SQLModel.metadata.create_all(engine)
   yield engine
   SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session(engine):
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            yield session
            for table in reversed(SQLModel.metadata.sorted_tables):
                session.exec(table.delete())
            session.commit()

@pytest.fixture()
def client(app, session):
    import datasource.database as db_module

    def override_get_session():
        yield session

    app.dependency_overrides[db_module.get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
