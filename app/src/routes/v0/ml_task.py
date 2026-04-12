import logging
import services.user
import services.ml_task
import services.transaction
import services.ml_task
from fastapi import APIRouter, HTTPException, Path
from fastapi.params import Depends
from starlette import status
from database.database import get_session
from models.ml_task import MLTask


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

task_route = APIRouter()


@task_route.get("/{task_id}/",
                response_model=MLTask,
                status_code=status.HTTP_200_OK,
                summary="ML task",
                description="Get ML task data by task id")
async def get_ml_task(task_id: int = Path(..., description="task id"),
                      session=Depends(get_session)) -> MLTask:
    try:
        ml_task = services.ml_task.get_ml_task_by_id(task_id, session)
        return ml_task
    except Exception as e:
        logger.error(f"Error getting ML task: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the ML task by id")
