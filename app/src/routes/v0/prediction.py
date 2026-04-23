import logging
import services.repository.prediction
from fastapi import APIRouter, HTTPException, Path
from fastapi.params import Depends
from starlette import status
from datasource.database import get_session
from models.prediction import Prediction
from auth.authenticate import authenticate
from models.user import UserRole

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

prediction_route = APIRouter()


@prediction_route.get("/{prediction_id}/",
                response_model=Prediction,
                status_code=status.HTTP_200_OK,
                summary="Prediction",
                description="Get prediction data by prediction id")
async def get_prediction(prediction_id: int = Path(..., description="prediction id"),
                         session=Depends(get_session), current_login = Depends(authenticate)) -> Prediction:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        prediction = services.repository.prediction.get_prediction_by_id(prediction_id, session)
        return prediction
    except Exception as e:
        logger.error(f"Error getting prediction: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the prediction by id")
