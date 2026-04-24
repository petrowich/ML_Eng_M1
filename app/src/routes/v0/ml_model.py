import logging
from decimal import Decimal
import services.repository.ml_model
from typing import List
from fastapi import APIRouter, HTTPException, Body, Path
from fastapi.params import Depends
from starlette import status
from datasource.database import get_session
from models.ml_model import MLModel
from pydantic import Field, BaseModel
from auth.authenticate import authenticate
from models.user import UserRole

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

model_route = APIRouter()


@model_route.get("/{model_id}/",
                response_model=MLModel,
                status_code=status.HTTP_200_OK,
                summary="ML Model",
                description="Get ML model data by model id")
async def get_ml_model(model_id: int = Path(..., description="model id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> MLModel:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        ml_model = services.repository.ml_model.get_ml_model_by_id(model_id, session)
        return ml_model
    except Exception as e:
        logger.error(f"Error getting ML model: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the ML model by id")


class RegisterMLModelRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=50, description="ML model external reference")
    name: str = Field(..., max_length=255, description="ML model name")
    description: str = Field(..., max_length=2000, description="ML model description")
    prediction_cost: float = Field(..., gt=0, description="prediction cost")

@model_route.post("/register",
                  response_model=MLModel,
                  status_code=status.HTTP_201_CREATED,
                  summary="Register ML Model",
                  description="Register new or update existent ML model")
async def register_ml_model(request: RegisterMLModelRequest = Body(...), session=Depends(get_session), current_login = Depends(authenticate)) -> MLModel:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")

        ml_model = services.repository.ml_model.get_ml_model_by_reference(request.model, session)

        if not ml_model:
            ml_model = MLModel(reference=request.model)

        ml_model.name = request.name
        ml_model.description = request.description
        ml_model.prediction_cost = Decimal(str(request.prediction_cost))

        ml_model = services.repository.ml_model.add_ml_model(ml_model, session)

        return ml_model
    except Exception as e:
        logger.error(f"Error registering ML model: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to registere ML model")

@model_route.get("/get_all",
                response_model=List[MLModel],
                status_code=status.HTTP_200_OK,
                summary="All ML models",
                description="List of all ML models")
async def get_all(session=Depends(get_session), current_login = Depends(authenticate)) -> List[MLModel]:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")

        ml_models = services.repository.ml_model.get_all_ml_models(session)
        return list(ml_models)
    except Exception as e:
        logger.error(f"Error getting all ML models: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get all ML models")
