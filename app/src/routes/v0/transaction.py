import logging
import uuid
import services.repository.transaction
from fastapi import APIRouter, HTTPException, Path
from fastapi.params import Depends
from starlette import status
from datasource.database import get_session
from models.transaction import Transaction
from auth.authenticate import authenticate
from models.user import UserRole

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

transaction_route = APIRouter()


@transaction_route.get("/{transaction_id}/",
                response_model=Transaction,
                status_code=status.HTTP_200_OK,
                summary="Transaction",
                description="Get transaction data by transaction id")
async def get_transaction(transaction_id: str = Path(..., description="transaction id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> Transaction:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        transaction_uuid = uuid.UUID(transaction_id)
        transaction = services.repository.transaction.get_transaction_by_id(transaction_uuid, session)
        return transaction
    except Exception as e:
        logger.error(f"Error getting transaction: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get the transaction")

@transaction_route.post("/{transaction_id}/apply",
                response_model=Transaction,
                status_code=status.HTTP_200_OK,
                summary="Apply transaction",
                description="Apply pending transaction")
async def apply_transaction(transaction_id: str = Path(..., description="transaction id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> Transaction:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        transaction_uuid = uuid.UUID(transaction_id)
        transaction = services.repository.transaction.get_transaction_by_id(transaction_uuid, session)
        transaction = services.repository.transaction.apply_transaction(transaction, session)
        return transaction
    except Exception as e:
        logger.error(f"Error applying transaction: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to apply transaction: {str(e)}")

@transaction_route.post("/{transaction_id}/cancel",
                response_model=Transaction,
                status_code=status.HTTP_200_OK,
                summary="Cancel transaction",
                description="Cancel pending transaction")
async def cancel_transaction(transaction_id: str = Path(..., description="transaction id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> Transaction:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        transaction_uuid = uuid.UUID(transaction_id)
        transaction = services.repository.transaction.get_transaction_by_id(transaction_uuid, session)
        transaction = services.repository.transaction.cancel_transaction(transaction, session)
        return transaction
    except Exception as e:
        logger.error(f"Error cancelling transaction: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to cancel transaction: {str(e)}")

@transaction_route.post("/{transaction_id}/refund",
                response_model=Transaction,
                status_code=status.HTTP_200_OK,
                summary="Refund transaction",
                description="Refund completed transaction")
async def refund_transaction(transaction_id: str = Path(..., description="transaction id"),
                      session=Depends(get_session), current_login = Depends(authenticate)) -> Transaction:
    try:
        if not current_login or current_login.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Forbidden")
        transaction_uuid = uuid.UUID(transaction_id)
        transaction = services.repository.transaction.get_transaction_by_id(transaction_uuid, session)
        transaction = services.repository.transaction.refund_transaction(transaction, session)
        return transaction
    except Exception as e:
        logger.error(f"Error refunding transaction: '{str(e)}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to refund transaction: {str(e)}")
