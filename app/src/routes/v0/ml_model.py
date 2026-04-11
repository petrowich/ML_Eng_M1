import logging
import services.user
import services.ml_model
import services.ml_model
import services.transaction
import services.ml_task
from typing import List
from fastapi import APIRouter, HTTPException, Body, Path
from fastapi.params import Depends
from starlette import status
from database.database import get_session
from models.ml_model import MLModel
from models.ml_task import MLTask
from pydantic import Field, BaseModel


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

model_route = APIRouter()


@model_route.get("/{model_id}/",
                response_model=MLModel,
                status_code=status.HTTP_200_OK,
                summary="ML Model",
                description="Get ML model data by model id")
async def get_ml_model(model_id: int = Path(..., description="model id"),
                      session=Depends(get_session)) -> MLModel:
    try:
        ml_model = services.ml_model.get_ml_model_by_id(model_id, session)
        return ml_model
    except Exception as e:
        logger.error(f"Error getting ML model: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the ML model by id")

@model_route.get("/get_all",
                response_model=List[MLModel],
                status_code=status.HTTP_200_OK,
                summary="All ML models",
                description="List of all ML models")
async def get_all(session=Depends(get_session)) -> List[MLModel]:
    try:
        ml_models = services.ml_model.get_all_ml_models(session)
        return list(ml_models)
    except Exception as e:
        logger.error(f"Error getting all ML models: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get all ML models")

class MLTaskRequest(BaseModel):
    user_id: int = Field(..., description="User id"),
    request: str = Field(..., description="Запрос к ML Модели")

@model_route.post("/{model_id}/task",
                  response_model=MLTask,
                  status_code=status.HTTP_201_CREATED,
                  summary="New ML task",
                  description="Create new ML task")
async def create_mal_task(model_id: int = Path(..., description="user id"),
                  request: MLTaskRequest = Body(...),
                  session=Depends(get_session)) -> MLTask:
    try:
        user = services.user.get_user_by_id(request.user_id, session)
        ml_model = services.ml_model.get_ml_model_by_id(model_id, session)

        balance = user.balance if user.balance else 0
        prediction_cost = ml_model.prediction_cost if ml_model.prediction_cost else 0
        if balance <= prediction_cost:
            logger.warning(f"Insufficient funds")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient funds")

        ml_task = services.ml_task.create_ml_task(MLTask(user=user, model=ml_model, request=request.request), session)
        return ml_task
    except Exception as e:
        logger.error(f"Error creating ML model: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ML model")
