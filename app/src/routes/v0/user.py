import logging
import services.user
import services.transaction
import services.ml_model
import services.ml_task
import services.prediction
from decimal import Decimal
from typing import List
from fastapi import APIRouter, HTTPException, Body, Path
from fastapi.params import Depends
from starlette import status
from database.database import get_session
from models.ml_task import MLTask
from models.prediction import Prediction
from models.transaction import Transaction, TransactionType
from models.user import User, UserAuth, UserRole
from pydantic import Field, BaseModel


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

user_route = APIRouter()


class UserAuthRequest(BaseModel):
    login: str = Field(..., description="User login")
    email: str = Field(..., description="User email")
    pwd_hash: str = Field(..., description="password")

class UserAuthResponse(BaseModel):
    message: str = Field(description="Response message")

@user_route.post("/signup",
                 response_model=UserAuthResponse,
                 status_code=status.HTTP_201_CREATED,
                 summary="User registration",
                 description="Register a new user")
async def signup(request: UserAuthRequest = Body(...),
                 session=Depends(get_session)) -> UserAuthResponse:
    try:
        if services.user.get_user_by_login(request.login, session):
            logger.warning(f"User login '{request.login}' already exists")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login '{request.login}' is already in use")

        if services.user.get_user_by_email(request.email, session):
            logger.warning(f"User email '{request.email}' is already registered")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email '{request.email}' is already registered")

        auth = UserAuth(login=request.login, pwd_hash=request.pwd_hash)
        user = User(auth=auth, email=request.email)
        services.user.add_user(user, session)

        logger.info(f"New user with login '{request.login}' created")

        return UserAuthResponse(message="User created successfully")
    except Exception as e:
        logger.error(f"Error signing up: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signup")

@user_route.post("/signin",
                 response_model=UserAuthResponse,
                 status_code=status.HTTP_200_OK,
                 summary="User authentication",
                 description="Authenticate user with provided credentials")
async def signin(request: UserAuthRequest = Body(...),
                 session=Depends(get_session)) -> UserAuthResponse:
    try:
        user = services.user.get_user_by_login(request.login, session)

        if not user:
            user = services.user.get_user_by_email(request.login, session)

        if not user:
            logger.warning(f"Trying to sign in with non-existent login name or email: '{request.login}'")
            raise HTTPException(status_code=status.HTTP_401, detail="Wrong login name or email")

        auth = user.auth

        if not auth or auth.pwd_hash != request.pwd_hash:
            logger.warning(f"Trying to sign in with wrong credentials")
            raise HTTPException(status_code=status.HTTP_403, detail="Wrong credentials")

        return UserAuthResponse(message=f"Authenticated successfully: '{user}'")
    except Exception as e:
        logger.error(f"Error signing in: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signin")

@user_route.get("/{user_id}/",
                response_model=User,
                status_code=status.HTTP_200_OK,
                summary="User",
                description="Get user data by user id")
async def get_user(user_id: int = Path(..., description="user id"),
                   session=Depends(get_session)) -> User:
    try:
        user = services.user.get_user_by_id(user_id, session)
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
                 session=Depends(get_session)) -> User:
    try:
        user = services.user.get_user_by_id(user_id, session)

        if user.email!=request.email and services.user.get_user_by_email(request.email, session):
            logger.warning(f"User email '{request.email}' is already registered")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email '{request.email}' is already registered")

        user.name = request.name
        user.email = request.email
        user.role = request.role
        user = services.user.add_user(user, session)

        return user
    except Exception as e:
        logger.error(f"Error signing in: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to signin")


class BalanceResponse(BaseModel):
    balance: float = Field(..., description="Current balance")

@user_route.get("/{user_id}/balance",
                response_model=BalanceResponse,
                status_code=status.HTTP_200_OK,
                summary="User balance",
                description="Get current user balance by user id")
async def get_balance(user_id: int = Path(..., description="user id"),
                      session=Depends(get_session)) -> BalanceResponse:
    try:
        user = services.user.get_user_by_id(user_id, session)
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
                  session=Depends(get_session)) -> DepositResponse:
    try:
        user = services.user.get_user_by_id(user_id, session)
        transaction = Transaction(user=user, type=TransactionType.DEPOSIT, amount=request.amount)
        services.transaction.add_transaction(transaction, session)
        services.transaction.apply_transaction(transaction, session)
        user = services.user.get_user_by_id(user_id, session)
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
async def get_all_users(session=Depends(get_session)) -> List[User]:
    try:
        users = services.user.get_all_users(session)
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
                             session=Depends(get_session)) -> List[MLTask]:
    try:
        user = services.user.get_user_by_id(user_id, session)
        ml_task = services.ml_task.get_ml_tasks_by_user(user, session)
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
                         session=Depends(get_session)) -> MLTask:
    try:
        user = services.user.get_user_by_id(user_id, session)
        ml_model = services.ml_model.get_ml_model_by_reference(request.model, session)

        if not ml_model:
            logger.warning(f"ML Model external reference '{request.model}' not found")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Wrong ML Model external reference: '{request.model}'")

        balance = user.balance if user.balance else 0
        prediction_cost = ml_model.prediction_cost if ml_model.prediction_cost else Decimal(0.0)

        if balance <= prediction_cost:
            logger.warning(f"Insufficient funds")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient funds")

        ml_task = services.ml_task.add_ml_task(MLTask(user=user, model=ml_model, request=request.request), session)

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
                               session=Depends(get_session)) -> List[Prediction]:
    try:
        user = services.user.get_user_by_id(user_id, session)
        predictions = services.prediction.get_predictions_by_user(user, session)
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
                               session=Depends(get_session)) -> List[Transaction]:
    try:
        user = services.user.get_user_by_id(user_id, session)
        transactions = services.transaction.get_transactions_by_user(user, session)
        return list(transactions)
    except Exception as e:
        logger.error(f"Error getting user transactions: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user transactions")
