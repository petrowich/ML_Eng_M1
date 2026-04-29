import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session
from models.ml_model import MLModel
from models.ml_task import MLTask
from models.transaction import Transaction, TransactionType, TransactionStatus
from models.user import User
from services.repository.transaction import add_transaction, get_transaction_by_id, add_transactions, \
    get_all_transactions, \
    delete_transaction, delete_transactions, get_transactions_by_user, apply_transaction, cancel_transaction, \
    refund_transaction


def create_test_user(session: Session, user_name="test user", user_email="email", balance: Decimal = None) -> User:
    user = User(name=user_name, email=user_email, balance=balance)
    session.add(user)
    return user

def create_test_ml_task(session: Session, user_name="test user", user_email="email", model_ref="MODEL_TEST", model_name="test model", balance: Decimal = None) -> MLTask:
    user = User(name=user_name, email=user_email, balance=balance)
    session.add(user)
    ml_model = MLModel(reference=model_ref, name=model_name)
    session.add(ml_model)
    ml_task = MLTask(user=user, ml_model=ml_model)
    session.add(ml_task)
    session.flush()
    return ml_task

def test_get_transaction_by_id(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    added_transaction = add_transaction(transaction, session)
    assert isinstance(added_transaction, Transaction)
    assert added_transaction.user.name == "test user"
    assert added_transaction.amount == Decimal("10.1")
    assert added_transaction.balance == Decimal("101.1")

def test_get_transaction_by_id_not_found(session: Session):
    with pytest.raises(ValueError):
        get_transaction_by_id(uuid.uuid4(), session)

def test_add_transaction(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    added_transaction = add_transaction(transaction, session)
    retrieved = get_transaction_by_id(added_transaction.id, session)
    assert isinstance(retrieved, Transaction)
    assert retrieved.id == added_transaction.id
    assert retrieved.user.name == "test user"
    assert retrieved.amount == Decimal("10.1")
    assert retrieved.balance == Decimal("101.1")

def test_add_transactions(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction_01 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transaction_02 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transactions = [transaction_01, transaction_02]
    added_transactions = add_transactions(transactions, session)
    assert len(added_transactions) == 2
    assert all(transaction.id is not None for transaction in added_transactions)
    all_tasks = get_all_transactions(session)
    assert len(all_tasks) == 2

def test_delete_transaction(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction_01 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transaction_02 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transactions = [transaction_01, transaction_02]
    add_transactions(transactions, session)
    delete_transaction(transaction_01, session)
    with pytest.raises(ValueError):
        get_transaction_by_id(transaction_01.id, session)

def test_delete_transactions(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction_01 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transaction_02 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transactions = [transaction_01, transaction_02]
    add_transactions(transactions, session)
    delete_transactions(transactions, session)
    all_tasks = get_all_transactions(session)
    assert len(all_tasks) == 0

def test_get_all_transactions(session: Session):
    user = create_test_user(session, "test user", "test@t.t", Decimal("101.1"))
    transaction_01 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    transaction_02 = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.1"))
    tasks = [transaction_01, transaction_02]
    add_transactions(tasks, session)
    all_transactions = get_all_transactions(session)
    assert len(all_transactions) == 2
    assert all(isinstance(transaction, Transaction) for transaction in all_transactions)
    assert all(transaction.user.name == "test user" for transaction in all_transactions)

def test_get_transactions_by_user(session: Session):
    user_01 = create_test_user(session, "test user 1", "test1@t.t", Decimal("101.1"))
    user_02 = create_test_user(session, "test user 2", "test2@t.t", Decimal("1.01"))
    transaction_01 = Transaction(user=user_01, type=TransactionType.WITHDRAW, amount=Decimal("0.5"))
    transaction_02 = Transaction(user=user_01, type=TransactionType.WITHDRAW, amount=Decimal("0.5"))
    transaction_03 = Transaction(user=user_02, type=TransactionType.WITHDRAW, amount=Decimal("0.5"))
    transactions = [transaction_01, transaction_02, transaction_03]
    add_transactions(transactions, session)
    retrieved = get_transactions_by_user(user_01, session)
    assert len(retrieved) == 2
    assert all(isinstance(transaction, Transaction) for transaction in retrieved)
    assert any(transaction.user.name == "test user 1" for transaction in retrieved)



def test_apply_transaction_deposit(session: Session):
    user = create_test_user(session, user_name="test user", user_email="u1@t.t", balance=Decimal("100.0"))
    transaction = Transaction(user=user, type=TransactionType.DEPOSIT,amount=Decimal("10.50"), status=TransactionStatus.PENDING)
    add_transaction(transaction, session)
    applied = apply_transaction(transaction, session)
    assert applied.status == TransactionStatus.COMPLETED
    assert applied.balance == Decimal("110.50")
    assert applied.timestamp is not None
    session.refresh(user)
    assert user.balance == Decimal("110.50")


def test_apply_transaction_withdraw(session: Session):
    user = create_test_user(session, user_name="test user", user_email="u1@t.t", balance=Decimal("100.0"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW,amount=Decimal("30.00"), status=TransactionStatus.PENDING)
    add_transaction(transaction, session)
    applied = apply_transaction(transaction, session)
    assert applied.status == TransactionStatus.COMPLETED
    assert applied.balance == Decimal("70.00")
    session.refresh(user)
    assert user.balance == Decimal("70.00")


def test_apply_transaction_invalid_status(session: Session):
    user = create_test_user(session, user_name="test user", user_email="u1@t.t", balance=Decimal("10.0"))
    transaction = Transaction(user=user, type=TransactionType.DEPOSIT, amount=Decimal("1.00"), status=TransactionStatus.COMPLETED)
    add_transaction(transaction, session)
    with pytest.raises(ValueError):
        apply_transaction(transaction, session)

def test_cancel_transaction_success(session: Session):
    user = create_test_user(session, user_name="test user", user_email="u1@t.t", balance=Decimal("55.0"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.00"), status=TransactionStatus.PENDING)
    add_transaction(transaction, session)
    cancelled = cancel_transaction(transaction, session)
    assert cancelled.status == TransactionStatus.CANCELLED
    assert cancelled.balance == Decimal("55.00")
    assert cancelled.timestamp is not None
    session.refresh(user)
    assert user.balance == Decimal("55.00")

def test_cancel_transaction_invalid_status(session: Session):
    user = create_test_user(session, "cancel user2", "cancel2@t.t", Decimal("55.00"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("10.00"), status=TransactionStatus.COMPLETED)
    add_transaction(transaction, session)
    with pytest.raises(ValueError):
        cancel_transaction(transaction, session)

def test_refund_transaction_deposit(session: Session):
    user = create_test_user(session, "refund user", "refund@t.t", Decimal("100.00"))
    transaction = Transaction(user=user, type=TransactionType.DEPOSIT, amount=Decimal("10.00"), status=TransactionStatus.COMPLETED)
    add_transaction(transaction, session)
    refunded = refund_transaction(transaction, session)
    assert refunded.status == TransactionStatus.REFUNDED
    assert refunded.balance == Decimal("90.00")
    assert refunded.timestamp is not None
    session.refresh(user)
    assert user.balance == Decimal("90.00")

def test_refund_transaction_withdraw(session: Session):
    user = create_test_user(session, "refund user2", "refund2@t.t", Decimal("70.00"))
    transaction = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("20.00"), status=TransactionStatus.COMPLETED)
    add_transaction(transaction, session)
    refunded = refund_transaction(transaction, session)
    assert refunded.status == TransactionStatus.REFUNDED
    assert refunded.balance == Decimal("90.00")
    session.refresh(user)
    assert user.balance == Decimal("90.00")

def test_refund_transaction_invalid_status(session: Session):
    user = create_test_user(session, "refund user3", "refund3@t.t", Decimal("70.00"))
    tx = Transaction(user=user, type=TransactionType.WITHDRAW, amount=Decimal("20.00"),  status=TransactionStatus.PENDING)
    add_transaction(tx, session)
    with pytest.raises(ValueError):
        refund_transaction(tx, session)
