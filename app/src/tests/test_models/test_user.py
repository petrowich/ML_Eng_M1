import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.user import UserAuth, User, UserRole

def test_valid_user_auth_minimal():
    user_auth = UserAuth(login="test", pwd_hash="hash")
    assert isinstance(user_auth, UserAuth)
    assert user_auth.login == "test"
    assert user_auth.pwd_hash == "hash"
    assert user_auth.user_id is None
    assert user_auth.user is None
    assert isinstance(user_auth.changed, datetime)
    assert user_auth.changed.tzinfo == timezone.utc

def test_missing_login():
    user_auth = UserAuth(pwd_hash="hash")
    with pytest.raises(ValidationError) as exc_info:
        UserAuth.model_validate(user_auth)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('login',)

def test_missing_pwd_hash():
    user_auth = UserAuth(login="test")
    with pytest.raises(ValidationError) as exc_info:
        UserAuth.model_validate(user_auth)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_type'
    assert errors[0]['loc'] == ('pwd_hash',)

def test_pwd_hash_too_long():
    long_hash = "a" * 256
    user_auth = UserAuth(login="test", pwd_hash=long_hash)
    with pytest.raises(ValidationError) as exc_info:
        UserAuth.model_validate(user_auth)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('pwd_hash',)

def test_valid_user_minimal():
    user = User(name="test", email="test@example.com")
    assert isinstance(user, User)
    assert user.name == "test"
    assert user.email == "test@example.com"
    assert user.role == UserRole.USER
    assert user.balance is None
    assert user.id is None
    assert user.auth is None
    assert user.ml_tasks == []
    assert user.transactions == []
    assert isinstance(user.created, datetime)
    assert user.created.tzinfo == timezone.utc

def test_name_empty_string():
    user = User(name="", email="test@example.com")
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_short'
    assert errors[0]['loc'] == ('name',)

def test_name_too_long():
    long_name = "a" * 256
    user = User(name=long_name, email="test@example.com")
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('name',)

def test_email_too_short():
    user = User(name="test", email="ab")
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_short'
    assert errors[0]['loc'] == ('email',)

def test_email_too_long():
    long_email = "a" * 256
    user = User(name="test", email=long_email)
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'string_too_long'
    assert errors[0]['loc'] == ('email',)

def test_role_invalid():
    user = User(name="test", email="test@example.com", role="INVALID")
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'enum'
    assert errors[0]['loc'] == ('role',)

def test_balance_invalid_type():
    user = User(name="test", email="test@example.com", balance="invalid")
    with pytest.raises(ValidationError) as exc_info:
        User.model_validate(user)
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'decimal_parsing'
    assert errors[0]['loc'] == ('balance',)
