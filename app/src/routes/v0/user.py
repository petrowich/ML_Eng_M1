import logging

from sqlmodel import Session

import services.repository.transaction
import services.repository.ml_model
import services.repository.ml_task
import services.repository.prediction
import services.repository.user
import services.mq.ml_task
import base64
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body, Path, Request
from fastapi.params import Depends
from starlette import status
from auth.oauth2 import create_access_token
from datasource.database import get_session
from models.ml_task import MLTask, MLTaskStatus
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType
from models.user import User, UserAuth, UserRole
from pydantic import Field, BaseModel
from auth.hash import create_hash, verify_hash
from auth.authenticate import authenticate
from fastapi.security.utils import get_authorization_scheme_param

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_route = APIRouter()
security = HTTPBasic()

class UserSignupRequest(BaseModel):
    login: str = Field(..., description="User login")
    email: str = Field(..., description="User email")
    password: str = Field(..., description="password")

class UserAuthResponse(BaseModel):
    message: str = Field(description="Response message")

class UserSigninRequest(BaseModel):
   username: str = Field(..., description="Login or email")
   password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    access_token: str = Field(description="Access token")
    token_type: str = "Bearer"

@user_route.post("/signup",
                 response_model=UserAuthResponse,
                 status_code=status.HTTP_201_CREATED,
                 summary="User registration",
                 description="Register a new user")
async def signup(request: UserSignupRequest = Body(...),
                 session: Session = Depends(get_session)) -> UserAuthResponse:
    try:
        if services.repository.user.get_user_by_login(request.login, session):
            logger.warning(f"User login '{request.login}' already exists")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Login '{request.login}' is already in use")

        if services.repository.user.get_user_by_email(request.email, session):
            logger.warning(f"User email '{request.email}' is already registered")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{request.email}' is already registered")

        password_hash = create_hash(request.password)
        user_auth = UserAuth(login=request.login, pwd_hash=password_hash)
        user = User(auth=user_auth, email=request.email)
        services.repository.user.add_user(user, session)

        logger.info(f"New user with login '{request.login}' created")
        session.commit()

        return UserAuthResponse(message="User created successfully")
    except Exception as e:
        logger.error(f"Error signup: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signup")

def optional_basic_credentials(request: Request) -> Optional[HTTPBasicCredentials]:
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        return None

    scheme, param = get_authorization_scheme_param(authorization)
    if scheme.lower() != "basic":
        return None

    try:
        data = base64.b64decode(param).decode("ascii")
        username, separator, password = data.partition(":")
        if not separator:
            return None
        return HTTPBasicCredentials(username=username, password=password)
    except Exception:
        return None

@user_route.post("/signin",
                 response_model=TokenResponse,
                 status_code=status.HTTP_200_OK,
                 summary="User authentication",
                 description="Authenticate user with provided credentials")
async def signin(credentials: Optional[HTTPBasicCredentials] = Depends(optional_basic_credentials),
                 request: Optional[UserSigninRequest] = Body(None),
                 session = Depends(get_session)) -> TokenResponse:
    if credentials is not None:
        username = credentials.username
        password = credentials.password
    elif request is not None:
        username = request.username
        password = request.password
    else:
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide credentials via Basic Auth or JSON body")

    try:
        user = services.repository.user.get_user_by_login(username, session)

        if not user:
            user = services.repository.user.get_user_by_email(username, session)

        if not user:
            logger.warning(f"Trying to sign in with non-existent login name or email: '{username}'")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong login name or email")

        user_auth = user.auth

        if not user_auth or not verify_hash(password, user_auth.pwd_hash):
            logger.warning(f"Trying to signin with wrong credentials")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials")

        logger.info(f"Authenticated successfully: '{user}'")
        access_token = create_access_token(user_auth.login)
        return TokenResponse(access_token=access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error signing in: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signin")

@user_route.get("/{user_id}/",
                response_model=User,
                status_code=status.HTTP_200_OK,
                summary="User",
                description="Get user data by user id")
async def get_user(user_id: int = Path(..., description="user id"),
                   current_login = Depends(authenticate),
                   session=Depends(get_session)) -> User:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"get user error: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user by id")

class UserUpdateRequest(BaseModel):
    name: str = Field(max_length=255, description="User Name")
    email: str = Field(max_length=255, description="User email")
    role: UserRole = Field(default=UserRole.USER, description="User role")

@user_route.post("/{user_id}/update",
                 response_model=User,
                 status_code=status.HTTP_200_OK,
                 summary="Update user",
                 description="Update user data")
async def update(user_id: int = Path(..., description="user id"),
                 request: UserUpdateRequest = Body(...),
                 current_login = Depends(authenticate),
                 session: Session = Depends(get_session)) -> User:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        if user.email!=request.email and services.repository.user.get_user_by_email(request.email, session):
            logger.warning(f"User email '{request.email}' is already registered")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{request.email}' is already registered")

        user.name = request.name
        user.email = request.email
        user.role = request.role
        user = services.repository.user.add_user(user, session)

        session.commit()

        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating user: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to user update")


class BalanceResponse(BaseModel):
    balance: float = Field(..., description="Current balance")

@user_route.get("/{user_id}/balance",
                response_model=BalanceResponse,
                status_code=status.HTTP_200_OK,
                summary="User balance",
                description="Get current user balance by user id")
async def get_balance(user_id: int = Path(..., description="user id"),
                      current_login = Depends(authenticate),
                      session = Depends(get_session)) -> BalanceResponse:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        balance = user.balance if user.balance else Decimal(0.0)
        response = BalanceResponse(balance=float(balance))
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting balance: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve balance")


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Deposit amount")


class DepositResponse(BaseModel):
    deposited: float = Field(..., description="Deposited funds")
    balance: float = Field(..., description="Current balance")

@user_route.post("/{user_id}/deposit",
                 response_model=DepositResponse,
                 status_code=status.HTTP_201_CREATED,
                 summary="Deposit funds",
                 description="Deposit funds by user id")
async def deposit(user_id: int = Path(..., description="user id"),
                  request: DepositRequest = Body(...),
                  current_login = Depends(authenticate),
                  session: Session = Depends(get_session)) -> DepositResponse:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        transaction = Transaction(user=user, type=TransactionType.DEPOSIT, amount=request.amount)
        services.repository.transaction.add_transaction(transaction, session)
        services.repository.transaction.apply_transaction(transaction, session)
        user = services.repository.user.get_user_by_id(user_id, session)
        balance = user.balance if user.balance else Decimal(0.0)
        response = DepositResponse(deposited=request.amount, balance=float(balance))

        session.commit()

        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing deposit: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to deposit funds")

@user_route.get("/get_all",
                response_model=List[User],
                status_code=status.HTTP_200_OK,
                summary="All users",
                description="List of all users")
async def get_all_users(current_login=Depends(authenticate), session=Depends(get_session)) -> List[User]:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        users = services.repository.user.get_all_users(session)

        return list(users)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting all users: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get all users")

@user_route.get("/{user_id}/ml_tasks",
                response_model=List[MLTask],
                status_code=status.HTTP_200_OK,
                summary="User ML tasks",
                description="List of user ML tasks")
async def get_user_ml_tasks(user_id: int = Path(..., description="user id"),
                             current_login = Depends(authenticate),
                            session = Depends(get_session)) -> List[MLTask]:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        ml_task = services.repository.ml_task.get_ml_tasks_by_user(user, session)
        return list(ml_task)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting user ML tasks: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user ML tasks")


class CreateMLTaskRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=50, description="ML model external reference")
    request: str = Field(..., description="request content")

@user_route.post("/{user_id}/ml_task",
                  response_model=MLTask,
                  status_code=status.HTTP_201_CREATED,
                  summary="New ML task",
                  description="Create new ML task")
async def create_ml_task(user_id: int = Path(..., description="user id"),
                         request: CreateMLTaskRequest = Body(...),
                         current_login = Depends(authenticate),
                         session: Session = Depends(get_session)) -> MLTask:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        ml_model = services.repository.ml_model.get_ml_model_by_reference(request.model, session)

        if not ml_model:
            logger.warning(f"ML Model external reference '{request.model}' not found")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Wrong ML Model external reference: '{request.model}'")

        balance = user.balance if user.balance else 0
        prediction_cost = ml_model.prediction_cost if ml_model.prediction_cost else Decimal(0.0)

        if balance <= prediction_cost:
            logger.warning(f"Insufficient funds")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient funds")

        ml_task = services.repository.ml_task.add_ml_task(MLTask(user=user, ml_model=ml_model, request=request.request), session)

        try:
            correlation_id = services.mq.ml_task.publish_ml_task(ml_task)
            ml_task.status=MLTaskStatus.QUEUED
        except Exception as e:
            logger.error(f"Error processing ML task: '{str(e)}'")
            ml_task.status=MLTaskStatus.FAILED
            raise e

        ml_task = services.repository.ml_task.add_ml_task(ml_task, session)

        session.commit()

        return ml_task
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating ML task: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ML task")

@user_route.get("/{user_id}/predictions",
                response_model=List[Prediction],
                status_code=status.HTTP_200_OK,
                summary="User predictions",
                description="List of user predictions")
async def get_user_predictions(user_id: int = Path(..., description="user id"),
                               current_login = Depends(authenticate),
                               session = Depends(get_session)) -> List[Prediction]:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)

        predictions = services.repository.prediction.get_predictions_by_user(user, session)
        return list(predictions)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting user predictions: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user predictions")

@user_route.get("/{user_id}/transactions",
                response_model=List[Transaction],
                status_code=status.HTTP_200_OK,
                summary="User transactions",
                description="List of user transactions")
async def get_user_predictions(user_id: int = Path(..., description="user id"),
                               current_login = Depends(authenticate),
                               session = Depends(get_session)) -> List[Transaction]:
    try:
        if current_login:
            current_user = services.repository.user.get_user_by_login(current_login, session)
            if not current_user or current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no rights")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no login")

        user = services.repository.user.get_user_by_id(user_id, session)
        transactions = services.repository.transaction.get_transactions_by_user(user, session)
        return list(transactions)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting user transactions: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user transactions")
