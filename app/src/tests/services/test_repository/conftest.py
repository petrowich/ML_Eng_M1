import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import InvalidRequestError
from models.ml_model import MLModel
from models.ml_task import MLTask
from models.user import User
from models.prediction import Prediction
from models.transaction import Transaction

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
                session.execute(table.delete())
            session.commit()
