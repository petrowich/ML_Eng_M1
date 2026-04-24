import logging
import services.repository.user
import services.repository.transaction
import services.repository.ml_model
import services.repository.ml_task
from typing import List, Dict, Sequence
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from auth.oauth2 import get_current_user
from datasource.config import get_settings
from datasource.database import get_session
from models.ml_task import MLTask
from models.user import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ml_tasks_ui_route = APIRouter()

settings = get_settings()
templates = Jinja2Templates(directory="templates")

AUTH_TOKEN_COOKIE_NAME = settings.auth_token_cookie_name()


@ml_tasks_ui_route.get("/", response_class=HTMLResponse, summary="ML Tasks", description="ML tasks history")
async def ml_models_get(request: Request, current_user: User = Depends(get_current_user), session=Depends(get_session)):
    login = current_user.auth.login
    try:
        ml_tasks: Sequence[MLTask] = services.repository.ml_task.get_ml_tasks_by_user(current_user, session)
        ml_tasks = sorted(ml_tasks, key=lambda t: t.timestamp, reverse=True)

        tasks: List[Dict[str, str]] = [
            {"model_name": ml_task.ml_model.name or '',
             "datetime": ml_task.timestamp.strftime("%Y-%m-%d %H:%M:%S") or '',
             "request": ml_task.request or '',
             "status": ml_task.status.name.lower() or '',
             "duration": str(ml_task.duration_ms),
             "prediction": ml_task.prediction.result or '' if ml_task.prediction else ml_task.failure or '',
             "cost": str(ml_task.prediction.cost) or '' if ml_task.prediction else '0',
             } for ml_task in ml_tasks]

        context = {"request": request, "login": login, "tasks": tasks}
        return templates.TemplateResponse(request,"ml_tasks.html", context=context)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting tasks: {error_msg}")
        context={"request": request, "login": login, "error_msg": f"Error getting tasks: {error_msg}", "back_url": "/"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)
