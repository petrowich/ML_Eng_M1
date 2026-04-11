from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Sequence
from uuid import UUID

from sqlmodel import Session, select
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.user import User
from services.user import get_user_by_id


def get_transaction_by_id(transaction_id: UUID, session: Session) -> Transaction:
    try:
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        transaction = session.exec(stmt).first()
        if not transaction or not isinstance(transaction, Transaction):
            raise ValueError(f"Invalid transaction id:{transaction_id}")
        return transaction
    except Exception:
        raise

def apply_transaction(transaction: Transaction, session: Session) -> Transaction:
    try:
        transaction = get_transaction_by_id(transaction.id, session)
        if transaction.status!=TransactionStatus.PENDING:
            raise ValueError(f"Invalid transaction status {transaction.status}")

        user = transaction.user

        if not user or not user.id:
            raise ValueError("Invalid transaction user")

        user = get_user_by_id(user.id,  session)
        user_balance = user.balance if user.balance else Decimal(0.0)

        if transaction.type==TransactionType.DEPOSIT:
            user_balance += transaction.amount
        elif transaction.type==TransactionType.WITHDRAW:
            user_balance -= transaction.amount

        transaction.status = TransactionStatus.COMPLETED
        transaction.timestamp = datetime.now(timezone.utc)
        transaction.balance = user_balance
        user.balance = user_balance

        session.add(transaction)
        session.add(user)
        session.commit()
        session.refresh(transaction)
        return transaction
    except Exception:
        session.rollback()
        raise

def cancel_transaction(transaction: Transaction, session: Session):
    try:
        transaction = get_transaction_by_id(transaction.id, session)
        if transaction.status!=TransactionStatus.PENDING:
            raise ValueError(f"Invalid transaction status {transaction.status}")

        user = transaction.user

        if not user or not user.id:
            raise ValueError("Invalid transaction user")

        user = get_user_by_id(user.id,  session)
        user_balance = user.balance if user.balance else Decimal(0.0)

        transaction.status = TransactionStatus.CANCELLED
        transaction.timestamp = datetime.now(timezone.utc)
        transaction.balance = user_balance

        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction
    except Exception:
        session.rollback()
        raise

def refund_transaction(transaction: Transaction, session: Session) -> Transaction:
    try:
        transaction = get_transaction_by_id(transaction.id, session)
        if transaction.status!=TransactionStatus.COMPLETED:
            raise ValueError(f"Invalid transaction status {transaction.status}")

        user = transaction.user

        if not user or not user.id:
            raise ValueError("Invalid transaction user")

        user = get_user_by_id(user.id,  session)
        user_balance = user.balance if user.balance else Decimal(0.0)

        if transaction.type==TransactionType.DEPOSIT:
            user_balance -= transaction.amount
        elif transaction.type==TransactionType.WITHDRAW:
            user_balance += transaction.amount

        transaction.status = TransactionStatus.REFUNDED
        transaction.timestamp = datetime.now(timezone.utc)
        transaction.balance = user_balance
        user.balance = user_balance

        session.add(transaction)
        session.add(user)
        session.commit()
        session.refresh(transaction)
        return transaction
    except Exception:
        session.rollback()
        raise

def create_transaction(transaction: Transaction, session: Session) -> Transaction:
    try:
        transaction.balance = transaction.user.balance if transaction.user and transaction.user.balance else Decimal(0.0)
        session.add(transaction)
        session.commit()
        return transaction
    except Exception:
        session.rollback()
        raise

def update_transaction(transaction: Transaction, session: Session):
    try:
        session.add(transaction)
        session.commit()
    except Exception:
        session.rollback()
        raise

def create_transactions(transactions: Iterable[Transaction], session: Session) -> Iterable[Transaction]:
    try:
        for transaction in transactions:
            transaction.balance = transaction.user.balance if transaction.user and transaction.user.balance else Decimal(0.0)
        session.add_all([transaction for transaction in transactions])
        session.commit()
        for transaction in transactions:
            session.refresh(transaction)
        return transactions
    except Exception:
        session.rollback()
        raise

def delete_transaction(transaction: Transaction, session: Session):
    try:
        session.delete(transaction)
        session.commit()
    except Exception:
        session.rollback()
        raise

def delete_transactions(transactions: Iterable[Transaction], session: Session):
    try:
        for transaction in transactions:
            session.delete(transaction)
        session.commit()
    except Exception:
        session.rollback()
        raise

def get_all_transactions(session: Session) -> Sequence[Transaction]:
    try:
        stmt = select(Transaction)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_transactions_by_user(user: User, session: Session) -> Sequence[Transaction]:
    try:
        stmt = select(Transaction).join(User).where(User.id == user.id)
        return session.exec(stmt).all()
    except Exception:
        raise

def get_completed_withdraw_transactions_by_user(user: User, session: Session) -> Sequence[Transaction]:
    try:
        stmt = (select(Transaction).join(User)
                .where(User.id == user.id)
                .where(Transaction.type == TransactionType.WITHDRAW)
                .where(Transaction.status == TransactionStatus.COMPLETED))
        return session.exec(stmt).all()
    except Exception:
        raise