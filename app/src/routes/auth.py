import logging
from fastapi.security import OAuth2PasswordRequestForm
import services.repository.user
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from auth.hash import create_hash, verify_hash
from auth.oauth2 import create_access_token
from datasource.config import get_settings
from datasource.database import get_session
from models.user import UserAuth, User
from services.auth.loginform import LoginForm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()

auth_ui_route = APIRouter()
templates = Jinja2Templates(directory="templates")
AUTH_TOKEN_COOKIE_NAME = settings.auth_token_cookie_name()


@auth_ui_route.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm=Depends(), session=Depends(get_session)) -> dict[str, str]:
    try:
        user = services.repository.user.get_user_by_login(form_data.username, session)

        if not user:
            user = services.repository.user.get_user_by_email(form_data.username, session)

        if not user:
            logger.warning(f"Trying to get access token by non-existent login name or email: '{form_data.username}'")
            raise HTTPException(status_code=status.HTTP_401, detail="Wrong login name or email")

        user_auth = user.auth
        password_hash = create_hash(form_data.password)

        if not user_auth or verify_hash(user_auth.pwd_hash, password_hash):
            logger.warning(f"Trying to get access token with wrong credentials")

            raise HTTPException(status_code=status.HTTP_403, detail="Wrong credentials")

        access_token = create_access_token(user_auth.login)
        response.set_cookie(key=AUTH_TOKEN_COOKIE_NAME, value=f"Bearer {access_token}", httponly=True)

        return {AUTH_TOKEN_COOKIE_NAME: access_token, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Error getting access token: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get access token")

@auth_ui_route.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    try:
        context = {"request": request}
        return templates.TemplateResponse(request, "register.html", context)
    except Exception as e:
        logger.error(f"Error getting signup page: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get signup page")

@auth_ui_route.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request,
                      response: Response,
                      login: str = Form(...),
                      email: str = Form(...),
                      password: str = Form(...),
                      password_confirm: str = Form(...),
                      session=Depends(get_session)):
    try:
        if password != password_confirm:
            error_msg = "Passwords do not match"
            return templates.TemplateResponse(request=request,
                                              name="error.html",
                                              context={"error_msg": error_msg},
                                              status_code=status.HTTP_400_BAD_REQUEST)

        if services.repository.user.get_user_by_login(login, session):
            logger.warning(f"User login '{login}' already exists")
            error_msg = f"Login '{login}' is already in use"
            return templates.TemplateResponse(request=request,
                                              name="error.html",
                                              context={"error_msg": error_msg},
                                              status_code=status.HTTP_409_CONFLICT)

        if services.repository.user.get_user_by_email(email, session):
            logger.warning(f"User email '{email}' is already registered")
            error_msg = f"Email '{email}' is already registered"
            return templates.TemplateResponse(request=request,
                                              name="error.html",
                                              context={"error_msg": error_msg},
                                              status_code=status.HTTP_409_CONFLICT)

        password_hash = create_hash(password)
        user_auth = UserAuth(login=login, pwd_hash=password_hash)
        user = User(auth=user_auth, email=email)
        services.repository.user.add_user(user, session)

        logger.info(f"New user with login '{login}' created")

        access_token = create_access_token(user_auth.login)
        response = RedirectResponse("/", status.HTTP_303_SEE_OTHER)
        response.set_cookie(key=AUTH_TOKEN_COOKIE_NAME, value=f"Bearer {access_token}", httponly=True)
        logger.info("Signup successful!!!!")
        return response

    except Exception as e:
        logger.error(f"Error signup: '{str(e)}'")
        error_msg = "Failed to signup"
        return templates.TemplateResponse(request=request,
                                          name="error.html",
                                          context={"error_msg": error_msg},
                                          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@auth_ui_route.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    try:
        context = {"request": request}
        return templates.TemplateResponse(request, "login.html", context)
    except Exception as e:
        logger.error(f"Error getting login page: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get login page")

@auth_ui_route.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, session=Depends(get_session)):
    try:
        form = LoginForm(request)
        await form.load_data()
        if await form.is_valid():
            try:
                response = RedirectResponse("/", status.HTTP_302_FOUND)
                await login_for_access_token(response=response, form_data=form, session=session)
                logger.info("Login successful!!!!")
                return response
            except HTTPException as e:
                error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
                logger.error(f"Login failed: {error_msg}")
                return templates.TemplateResponse(request=request, name="error.html", context={"request": request, "error": f"Login failed: {error_msg}", "back_url": "/auth/login"})
        else:
            error_msg = " ".join(form.errors) if form.errors else "Invalid form data."
            logger.error(f"Invalid form: {error_msg}")
            return templates.TemplateResponse(request=request, name="error.html", context={"request": request, "error": f"Login failed: {error_msg}", "back_url": "/auth/login"})
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error during login: {error_msg}")
        return templates.TemplateResponse(request=request, name="error.html", context={"request": request, "error": f"Login failed: {error_msg}", "back_url": "/auth/login"})

@auth_ui_route.get("/logout", response_class=HTMLResponse)
async def login_get():
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.auth_token_cookie_name())
    return response
