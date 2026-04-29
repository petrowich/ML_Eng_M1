import pytest
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from models.user import User, UserRole, UserAuth
from services.repository.user import (
    get_user_by_id,
    add_user,
    add_users,
    delete_user,
    delete_users,
    get_all_users,
    get_user_by_email, get_user_auth_by_login, get_user_by_login, update_password_hash,
)

def test_get_user_by_id(session: Session):
    user = User(name="user", email="test@test")
    added_user = add_user(user, session)
    retrieved = get_user_by_id(added_user.id, session)
    assert isinstance(retrieved, User)
    assert retrieved.id == added_user.id
    assert retrieved.name == "user"
    assert retrieved.email == "test@test"
    assert retrieved.role == UserRole.USER

def test_get_user_by_id_not_found(session: Session):
    with pytest.raises(ValueError):
        get_user_by_id(999, session)

def test_add_user(session: Session):
    user = User(name="user", email="test@test")
    added_user = add_user(user, session)
    retrieved = get_user_by_id(added_user.id, session)
    assert retrieved.email == "test@test"

def test_email_field_constraints(session: Session):
    invalid_user = User(email=None)
    with pytest.raises(IntegrityError):
        add_user(invalid_user, session)

    add_user(User(email="test@test", name="user"), session)
    duplicate_user = User(email="test@test", name="duplicate user")
    with pytest.raises(IntegrityError):
        add_user(duplicate_user, session)

def test_add_users(session: Session):
    users = [User(email="test1@test", name="user 1"),
              User(email="test2@test", name="user 2")]
    added_users = add_users(users, session)
    assert len(added_users) == 2
    assert all(user.id is not None for user in added_users)

    all_users = get_all_users(session)
    assert len(all_users) == 2

def test_add_users_with_duplicates(session: Session):
    users = [User(email="test@test", name="user"),
              User(email="test@test", name="duplicate user")]
    with pytest.raises(IntegrityError):
        add_users(users, session)

def test_delete_user(session: Session):
    user_1 = User(email="test1@test", name="user 1")
    user_2 = User(email="test2@test", name="user 2")
    users = [user_1, user_2]
    add_users(users, session)
    delete_user(user_1, session)
    all_users = get_all_users(session)
    assert len(all_users) == 1
    with pytest.raises(ValueError):
        get_user_by_id(user_1.id, session)

def test_delete_users(session: Session):
    users = [User(email="test1@test", name="user 1"),
              User(email="test2@test", name="user 2")]
    add_users(users, session)
    delete_users(users, session)
    all_users = get_all_users(session)
    assert len(all_users) == 0

def test_get_all_users(session: Session):
    users = [User(email="test1@test", name="user 1"),
              User(email="test2@test", name="user 2")]
    add_users(users, session)
    all_users = get_all_users(session)
    assert len(all_users) == 2
    assert all(isinstance(user, User) for user in all_users)

def test_get_user_by_reference(session: Session):
    add_user(User(email="test@test", name="user") , session)
    add_user(User(email="required@test", name="required") , session)
    retrieved = get_user_by_email("required@test", session)
    assert retrieved is not None
    assert isinstance(retrieved, User)
    assert retrieved.name == "required"

def test_update_password_hash(session: Session):
    auth = UserAuth(login="login", pwd_hash="hash")
    user = add_user(User(email="test@test", name="user", auth=auth) , session)
    new_auth = user.auth
    new_auth.pwd_hash = "newhash"
    update_password_hash(auth , session)
    retrieved = get_user_by_id(user.id, session)
    assert isinstance(retrieved.auth, UserAuth)
    assert retrieved.auth.login == "login"
    assert retrieved.auth.pwd_hash == "newhash"

def test_get_user_auth_by_login(session: Session):
    auth = UserAuth(login="login", pwd_hash="hash")
    add_user(User(email="test@test", name="user", auth=auth) , session)
    retrieved = get_user_auth_by_login("login", session)
    assert isinstance(retrieved, UserAuth)
    assert retrieved.login == "login"
    assert retrieved.pwd_hash == "hash"

def test_get_user_by_login(session: Session):
    auth = UserAuth(login="login", pwd_hash="hash")
    add_user(User(email="test@test", name="user", auth=auth) , session)
    retrieved = get_user_by_login("login", session)
    assert isinstance(retrieved, User)
    assert retrieved.email == "test@test"
