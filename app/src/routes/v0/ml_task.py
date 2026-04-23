import logging
import services.repository.ml_task
from fastapi import APIRouter, HTTPException, Path
from fastapi.params import Depends
from starlette import status
from datasource.database import get_session
from models.ml_task import MLTask
from auth.authenticate import authenticate
from models.user import UserRole

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

task_route = APIRouter()


@task_route.get("/{task_id}/",
                response_model=MLTask,
                status_code=status.HTTP_200_OK,
                summary="ML task",
                description="Get ML task data by task id")
async def get_ml_task(task_id: int = Path(..., description="task id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> MLTask:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        ml_task = services.repository.ml_task.get_ml_task_by_id(task_id, session)
        return ml_task
    except Exception as e:
        logger.error(f"Error getting ML task: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the ML task by id")
