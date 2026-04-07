from sqlmodel import SQLModel, Session, create_engine
from database.config import get_settings

def get_engine():
    settings = get_settings()

    engine = create_engine(
        url=settings.database_url_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    return engine

def get_session(engine):
    with Session(engine) as session:
        yield session

def init_db(drop_all: bool = False):
    try:
        engine = get_engine()
        if drop_all:
            SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
    except Exception:
        raise

