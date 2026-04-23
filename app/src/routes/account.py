import logging
from typing import List, Dict

import services.repository.user
import services.repository.transaction
from starlette.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from auth.oauth2 import get_current_user
from datasource.config import get_settings
from datasource.database import get_session
from models.transaction import Transaction, TransactionType
from models.user import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

account_ui_route = APIRouter()

settings = get_settings()
templates = Jinja2Templates(directory="templates")

AUTH_TOKEN_COOKIE_NAME = settings.auth_token_cookie_name()

@account_ui_route.get("/", response_class=HTMLResponse, summary="Account", description="User account page")
async def account(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/auth/login/", status_code=302)
    login = current_user.auth.login
    context = {"request": request,
               "login": login,
               "user": current_user
               }
    return templates.TemplateResponse(request, name="account.html", context=context)

@account_ui_route.get("/profile", response_class=HTMLResponse, summary="Profile", description="User profile page")
async def profile_get(request: Request, current_user: User = Depends(get_current_user)):
    login = current_user.auth.login
    return templates.TemplateResponse(request,"profile.html", context={"request": request, "login": login, "user": current_user}
    )

@account_ui_route.post("/profile", response_class=HTMLResponse)
async def profile_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    login = current_user.auth.login
    try:
        if not name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")

        if len(name.strip())<3:
            raise HTTPException(status_code=400, detail="Name should be at least 3 characters long")

        if len(name.strip())>50:
            raise HTTPException(status_code=400, detail="Name cannot be more than 50 characters")

        if email != current_user.email:
            existing_user = services.repository.user.get_user_by_email(email, session)
            if existing_user:
                return templates.TemplateResponse(request,
                                                  name="error.html",
                                                  context={"request": request, "error": "Email is already in use", "back_url": "/profile"}
                                                  )
        current_user.name = name
        current_user.email = email
        user = services.repository.user.add_user(current_user, session)
        context = {"request": request,
                   "login": login,
                   "user": current_user
                   }
        return templates.TemplateResponse(request, name="account.html", context=context)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error update profile: {error_msg}")
        context={"request": request, "login": login, "error_msg": f"Error update profile: {error_msg}", "back_url": "/profile"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)

@account_ui_route.get("/deposit", response_class=HTMLResponse, summary="Deposit", description="Account replenish page")
async def profile_get(request: Request, current_user: User = Depends(get_current_user)):
    login = current_user.auth.login
    return templates.TemplateResponse(request,"deposit.html", context={"request": request, "login": login})

@account_ui_route.post("/deposit", response_class=HTMLResponse)
async def profile_post(request: Request, amount: int = Form(...), current_user: User = Depends(get_current_user), session=Depends(get_session)):
    login = current_user.auth.login
    try:
        transaction = Transaction(user=current_user, type=TransactionType.DEPOSIT, amount=amount)
        services.repository.transaction.add_transaction(transaction, session)
        services.repository.transaction.apply_transaction(transaction, session)
        context = {"request": request,
                   "login": login,
                   "user": current_user
                   }  
        return templates.TemplateResponse(request, name="account.html", context=context)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing deposit: {error_msg}")
        context={"request": request, "login": login, "error_msg": f"Error processing deposit: {error_msg}", "back_url": "/profile"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)


@account_ui_route.get("/transactions/", response_class=HTMLResponse)
async def get_transactions(request: Request, current_user: User = Depends(get_current_user), session=Depends(get_session)):
    login = current_user.auth.login
    try:
        transactions = services.repository.transaction.get_transactions_by_user(current_user, session)
        transactions = sorted(transactions, key=lambda t: t.timestamp, reverse=True)

        txs: List[Dict[str, str]] = [
            {"timestamp": transaction.timestamp.strftime("%Y-%m-%d %H:%M:%S") or '',
             "type": transaction.type.lower() or '',
             "status": transaction.status.lower() or '',
             "amount": str(transaction.amount) or '0',
             "balance": str(transaction.balance) or '0',
             } for transaction in transactions]

        context={"request": request, "login": login, "transactions": txs}
        return templates.TemplateResponse(request, name="transactions.html", context=context)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting transactions: {error_msg}")
        context={"request": request, "login": login, "error_msg": f"Error to get transactions: {error_msg}", "back_url": "/profile"}
        return templates.TemplateResponse(request=request, name="error.html", context=context)
