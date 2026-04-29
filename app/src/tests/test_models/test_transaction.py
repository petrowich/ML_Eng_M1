import pytest
from decimal import Decimal
from datetime import datetime, timezone
import uuid
from pydantic import ValidationError
from models.ml_model import MLModel
from models.transaction import Transaction, TransactionType, TransactionStatus


def test_valid_transaction_minimal():
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance=Decimal("100.0"))
    assert transaction.type == TransactionType.DEPOSIT
    assert transaction.amount == Decimal("10.0")
    assert transaction.balance == Decimal("100.0")
    assert isinstance(transaction.id, uuid.UUID)
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.ml_task is None
    assert isinstance(transaction.timestamp, datetime)
    assert transaction.timestamp.tzinfo == timezone.utc

def test_missing_transaction_type():
    transaction = Transaction(amount=Decimal("10.0"), balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'enum'
    assert errors[0]['loc'] == ('type',)

def test_type_invalid():
    transaction = Transaction(type="INVALID", amount=Decimal("10.0"), balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'enum'
    assert errors[0]['loc'] == ('type',)

def test_status_invalid():
    transaction = Transaction(type=TransactionType.DEPOSIT, status="INVALID", amount=Decimal("10.0"), balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'enum'
    assert errors[0]['loc'] == ('status',)

def test_missing_amount():
    transaction = Transaction(type=TransactionType.DEPOSIT, balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_type'
    assert errors[0]['loc'] == ('amount',)

def test_amount_invalid_type():
    transaction = Transaction(type=TransactionType.DEPOSIT, amount="invalid", balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_parsing'
    assert errors[0]['loc'] == ('amount',)

def test_amount_too_many_digits():
    invalid_amount = Decimal("123456789012345.12345")
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=invalid_amount, balance=Decimal("100.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_max_digits'
    assert errors[0]['loc'] == ('amount',)

def test_missing_balance():
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=Decimal("10.0"))
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_type'
    assert errors[0]['loc'] == ('balance',)

def test_balance_invalid_type():
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance="invalid")
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_parsing'
    assert errors[0]['loc'] == ('balance',)

def test_balance_too_many_digits():
    invalid_balance = Decimal("123456789012345.12345")
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance=invalid_balance)
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_max_digits'
    assert errors[0]['loc'] == ('balance',)

def test_id_invalid():
    transaction = Transaction(type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance=Decimal("100.0"), id="not-a-uuid")
    with pytest.raises(ValidationError) as exc_info:
        Transaction.model_validate(transaction)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'uuid_parsing'
    assert errors[0]['loc'] == ('id',)

def test_user_invalid():
    model = MLModel(name="not user")
    with pytest.raises(KeyError):
        Transaction(user=model, type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance=Decimal("100.0"), timestamp=789)
    with pytest.raises(AttributeError):
        Transaction(user="not user", type=TransactionType.DEPOSIT, amount=Decimal("10.0"), balance=Decimal("100.0"), timestamp=789)
