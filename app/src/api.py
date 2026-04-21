import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datasource.config import get_settings
from datasource.database import init_db
from datasource.rabbitmq import declare_queue, get_queue_ml_tasks
from routes.home import home_route
from routes.v0.ml_task import task_route
from routes.v0.ml_model import model_route
from routes.v0.prediction import prediction_route
from routes.v0.user import user_route
from routes.v0.transaction import transaction_route
from consumers.prediction import prediction_consumer

settings = get_settings()

APP_NAME = settings.APP_NAME or "unnamed ML service"
APP_DESCRIPTION = settings.APP_DESCRIPTION or ""
APP_PORT = settings.APP_PORT or 8080

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.cache = {}
        logger.info("initializing db")
        init_db(drop_all=True)
        logger.info("db has been initialized")
        logger.info("creating ML tasks queue")
        declare_queue(get_queue_ml_tasks())
        logger.info("ML tasks queue have been created")
        logger.info("starting prediction consumer")
        prediction_consumer.start()
        logger.info("prediction consumer has been created")

    except Exception as e:
        logger.error(f"start up failed: {e}")

    yield

    logger.info("stopping prediction consumer")
    prediction_consumer.stop()
    logger.info("prediction consumer has been stopped")

    app.state.cache.clear()
    logger.info("shutting down")

app = FastAPI(
    title = APP_NAME,
    description=APP_DESCRIPTION,
    version="0.1",
    docs_url="/api/v0/docs",
    redoc_url="/api/v0/redoc",
    lifespan=lifespan
    )

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(home_route, tags=["Home"])
app.include_router(user_route, prefix="/api/v0/users", tags=["Users"])
app.include_router(model_route, prefix="/api/v0/models", tags=["MLModel"])
app.include_router(task_route, prefix="/api/v0/tasks", tags=["MLTasks"])
app.include_router(transaction_route, prefix="/api/v0/transactions", tags=["Transaction"])
app.include_router(prediction_route, prefix="/api/v0/predictions", tags=["Predictions"])

if __name__ == '__main__':
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=APP_PORT,
        reload=True,
        workers=1,
        log_level="debug",
    )
