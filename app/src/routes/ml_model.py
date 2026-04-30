import logging
import time
from decimal import Decimal
from typing import List, Dict, Sequence
from sqlmodel import Session
from starlette.responses import RedirectResponse
import services.repository.user
import services.repository.transaction
import services.repository.ml_model
import services.repository.ml_task
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from auth.oauth2 import get_current_user
from datasource.config import get_settings
from datasource.database import get_session
from models.ml_model import MLModel
from models.ml_task import MLTask, MLTaskStatus
from models.user import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ml_models_ui_route = APIRouter()

settings = get_settings()
templates = Jinja2Templates(directory="templates")

AUTH_TOKEN_COOKIE_NAME = settings.auth_token_cookie_name()


@ml_models_ui_route.get("/", response_class=HTMLResponse, summary="ML Models", description="ML model request")
async def ml_models_get(request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not current_user:
        return RedirectResponse("/auth/login/", status_code=302)
    login = current_user.auth.login
    try:
        ml_models: Sequence[MLModel] = services.repository.ml_model.get_all_ml_models(session)
        models: List[Dict[str, str]] = [{"key": ml_model.reference or '', "value": ml_model.name or ''} for ml_model in ml_models]
        context = {"request": request, "login": login, "models": models}
        return templates.TemplateResponse(request,"ml_models.html", context=context)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing deposit: {error_msg}")
        context={"request": request, "login": login, "error_msg": f"Error processing deposit: {error_msg}", "back_url": "/"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)

@ml_models_ui_route.post("/submit_task", response_class=HTMLResponse, summary="Submit ML Task", description="Submit a new ML task")
async def submit_task(request: Request,
                                model: str = Form(...),
                                text: str = Form(...),
                                current_user: User = Depends(get_current_user),
                                session: Session =Depends(get_session),
                      ):
    if not current_user:
        return RedirectResponse("/auth/login/", status_code=302)
    login = current_user.auth.login
    try:
        if not model or not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model and text are required")

        ml_model = services.repository.ml_model.get_ml_model_by_reference(model, session)
        if not ml_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

        balance = current_user.balance if current_user.balance else 0
        prediction_cost = ml_model.prediction_cost if ml_model.prediction_cost else Decimal(0.0)

        if balance <= prediction_cost:
            logger.error(f"Insufficient funds")
            raise Exception("Insufficient funds!")

        user = services.repository.user.get_user_by_login(login, session)
        ml_task = MLTask(user=user, ml_model=ml_model, request=text)
        ml_task = services.repository.ml_task.add_ml_task(ml_task, session)

        session.commit()

        for attempt in range(1, 4):
            try:
                correlation_id = services.mq.ml_task.publish_ml_task(ml_task)
                break
            except Exception as e:
                if attempt >= 3:
                    logger.error(f"Error processing ML task: '{str(e)}'")
                    ml_task.status=MLTaskStatus.FAILED
                    services.repository.ml_task.add_ml_task(ml_task, session)
                    session.commit()
                    raise
                time.sleep(0.3 * attempt)

        ml_task.status=MLTaskStatus.QUEUED
        services.repository.ml_task.add_ml_task(ml_task, session)
        session.commit()
        logger.info(f"Queued ML task {ml_task.ml_model.reference} {ml_task.request}")

        return RedirectResponse(url="/ml_tasks", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error submitting task: {error_msg}")
        context = {"request": request, "login": login, "error": "Error submitting task", "error_msg": f"{error_msg}", "back_url": "/ml_models/"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)
