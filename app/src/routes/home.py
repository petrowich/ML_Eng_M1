import logging

from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

import services.repository.user
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from starlette import status
from auth.authenticate import authenticate_cookie
from datasource.config import get_settings
from datasource.database import get_session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

home_route = APIRouter()

settings = get_settings()
templates = Jinja2Templates(directory="templates")

AUTH_TOKEN_COOKIE_NAME = settings.auth_token_cookie_name()

@home_route.get("/", response_class=HTMLResponse, summary="Home", description="Home page")
async def index(request: Request, session=Depends(get_session)):
    token = request.cookies.get(AUTH_TOKEN_COOKIE_NAME)
    login = None
    user_name = None
    if token:
        try:
            if token.startswith("Bearer "):
                token = token.split("Bearer ")[1]
            login = await authenticate_cookie(token)
            user = services.repository.user.get_user_by_login(login, session)
            user_name = user.name
        except Exception as e:
            logger.error(f"Error authenticating token: '{str(e)}'")
            login = None
    context = {"login": login, "user_name": user_name, "request": request}
    return templates.TemplateResponse(request, "index.html", context)

class HealthResponse(BaseModel):
    status: str = Field(..., description="app status ")

@home_route.get("/health",
                response_model=HealthResponse,
                status_code=status.HTTP_200_OK,
                summary="Health check",
                description="App health status")
async def health() -> HealthResponse:
    try:
        return HealthResponse(status="healthy")
    except:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service is unavailable")