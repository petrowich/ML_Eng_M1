import logging
import services.repository.transaction
import services.repository.ml_model
import services.repository.ml_task
import services.repository.prediction
import services.repository.user
import services.mq.ml_task
from fastapi.security import OAuth2PasswordRequestForm
from decimal import Decimal
from typing import List, Dict
from fastapi import APIRouter, HTTPException, Body, Path
from fastapi.params import Depends
from starlette import status
from auth.oauth2 import create_access_token
from datasource.database import get_session
from datasource.rabbitmq import get_queue_ml_tasks, get_queue_predictions, get_channel
from models.ml_task import MLTask, MLTaskStatus
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType
from models.user import User, UserAuth, UserRole
from pydantic import Field, BaseModel
from auth.hash import create_hash, verify_hash
from auth.authenticate import authenticate


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_route = APIRouter()

class UserSignupRequest(BaseModel):
    login: str = Field(..., description="User login")
    email: str = Field(..., description="User email")
    password: str = Field(..., description="password")

class UserAuthResponse(BaseModel):
    message: str = Field(description="Response message")

@user_route.post("/signup",
                 response_model=UserAuthResponse,
                 status_code=status.HTTP_201_CREATED,
                 summary="User registration",
                 description="Register a new user")
async def signup(request: UserSignupRequest = Body(...),
                 session=Depends(get_session)) -> UserAuthResponse:
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

        return UserAuthResponse(message="User created successfully")
    except Exception as e:
        logger.error(f"Error signup: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signup")

@user_route.post("/signin",
                 response_model=UserAuthResponse,
                 status_code=status.HTTP_200_OK,
                 summary="User authentication",
                 description="Authenticate user with provided credentials")
async def signin(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)) -> Dict:
    try:
        user = services.repository.user.get_user_by_login(form_data.username, session)

        if not user:
            user = services.repository.user.get_user_by_email(form_data.username, session)

        if not user:
            logger.warning(f"Trying to sign in with non-existent login name or email: '{form_data.username}'")
            raise HTTPException(status_code=status.HTTP_401, detail="Wrong login name or email")

        user_auth = user.auth
        password_hash = create_hash(form_data.password)

        if not user_auth or verify_hash(user_auth.pwd_hash, password_hash):
            logger.warning(f"Trying to sign in with wrong credentials")
            raise HTTPException(status_code=status.HTTP_403, detail="Wrong credentials")

        logger.info(f"Authenticated successfully: '{user}'")
        access_token = create_access_token(user_auth.login)
        return {"access_token": access_token, "token_type": "Bearer"}
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
                   session=Depends(get_session), current_login=Depends(authenticate)) -> User:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        return user
    except Exception as e:
        logger.error(f"get user error: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to user by id")

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
                 session=Depends(get_session), current_login=Depends(authenticate)) -> User:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)

        if user.email!=request.email and services.repository.user.get_user_by_email(request.email, session):
            logger.warning(f"User email '{request.email}' is already registered")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{request.email}' is already registered")

        user.name = request.name
        user.email = request.email
        user.role = request.role
        user = services.repository.user.add_user(user, session)

        return user
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
                      session=Depends(get_session), current_login=Depends(authenticate)) -> BalanceResponse:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        balance = user.balance if user.balance else Decimal(0.0)
        response = BalanceResponse(balance=float(balance))
        return response
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
                  session=Depends(get_session), current_login=Depends(authenticate)) -> DepositResponse:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        transaction = Transaction(user=user, type=TransactionType.DEPOSIT, amount=request.amount)
        services.repository.transaction.add_transaction(transaction, session)
        services.repository.transaction.apply_transaction(transaction, session)
        user = services.repository.user.get_user_by_id(user_id, session)
        balance = user.balance if user.balance else Decimal(0.0)
        response = DepositResponse(deposited=request.amount, balance=float(balance))
        return response
    except Exception as e:
        logger.error(f"Error processing deposit: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to deposit funds")

@user_route.get("/get_all",
                response_model=List[User],
                status_code=status.HTTP_200_OK,
                summary="All users",
                description="List of all users")
async def get_all_users(session=Depends(get_session), current_login=Depends(authenticate)) -> List[User]:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        users = services.repository.user.get_all_users(session)
        return list(users)
    except Exception as e:
        logger.error(f"Error getting all users: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get all users")

@user_route.get("/{user_id}/ml_tasks",
                response_model=List[MLTask],
                status_code=status.HTTP_200_OK,
                summary="User ML tasks",
                description="List of user ML tasks")
async def get_user_ml_tasks(user_id: int = Path(..., description="user id"),
                             session=Depends(get_session), current_login=Depends(authenticate)) -> List[MLTask]:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        ml_task = services.repository.ml_task.get_ml_tasks_by_user(user, session)
        return list(ml_task)
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
                         session=Depends(get_session),
                         queue_ml_tasks=Depends(get_queue_ml_tasks),
                         queue_predictions=Depends(get_queue_predictions),
                         channel=Depends(get_channel), current_login=Depends(authenticate)) -> MLTask:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
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
            correlation_id = services.mq.ml_task.process_ml_task(ml_task, queue_ml_tasks, queue_predictions, channel)
            ml_task.status=MLTaskStatus.QUEUED
        except Exception as e:
            logger.error(f"Error processing ML task: '{str(e)}'")
            ml_task.status=MLTaskStatus.FAILED
            raise e

        ml_task = services.repository.ml_task.add_ml_task(ml_task, session)

        return ml_task
    except Exception as e:
        logger.error(f"Error creating ML task: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create ML task")

@user_route.get("/{user_id}/predictions",
                response_model=List[Prediction],
                status_code=status.HTTP_200_OK,
                summary="User predictions",
                description="List of user predictions")
async def get_user_predictions(user_id: int = Path(..., description="user id"),
                               session=Depends(get_session), current_login=Depends(authenticate)) -> List[Prediction]:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        predictions = services.repository.prediction.get_predictions_by_user(user, session)
        return list(predictions)
    except Exception as e:
        logger.error(f"Error getting user predictions: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user predictions")

@user_route.get("/{user_id}/transactions",
                response_model=List[Transaction],
                status_code=status.HTTP_200_OK,
                summary="User transactions",
                description="List of user transactions")
async def get_user_predictions(user_id: int = Path(..., description="user id"),
                               session=Depends(get_session), current_login=Depends(authenticate)) -> List[Transaction]:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        user = services.repository.user.get_user_by_id(user_id, session)
        transactions = services.repository.transaction.get_transactions_by_user(user, session)
        return list(transactions)
    except Exception as e:
        logger.error(f"Error getting user transactions: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user transactions")
