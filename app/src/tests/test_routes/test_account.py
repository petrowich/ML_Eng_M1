from decimal import Decimal

import services.repository.user
from models.user import User, UserAuth

def test_account_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/account/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_account_authorized_returns_200(client, app):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="Test User",
        auth=UserAuth(login="login", pwd_hash="hash"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.get("/account/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--account-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

def test_account_profile_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/account/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_account_profile_authorized_returns_200(client, app):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="Test User",
        auth=UserAuth(login="login", pwd_hash="hash"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.get("/account/profile")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--profile-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

def test_profile_post_unauthorized_returns_401(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.post(
        "/account/profile",
        data={"name": "New Name", "email": "new@example.test"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_profile_post_authorized_updates_user_and_returns_200(client, app, session):
    from auth.oauth2 import get_current_user
    user = User(
        email="old@example.test",
        name="Old Name",
        auth=UserAuth(login="test_login", pwd_hash="x"),
    )
    services.repository.user.add_user(user, session)
    session.commit()
    session.refresh(user)
    app.dependency_overrides[get_current_user] = lambda: user
    new_name = "New Name"
    new_email = "new@example.test"
    resp = client.post(
        "/account/profile",
        data={"name": new_name, "email": new_email},
        follow_redirects=False,
    )
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    updated = services.repository.user.get_user_by_login("test_login", session)
    assert updated is not None
    assert updated.name == new_name
    assert updated.email == new_email
    assert "<!--account-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

def test_account_deposit_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/account/deposit", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_account_deposit_authorized_returns_200(client, app):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="Test User",
        auth=UserAuth(login="login", pwd_hash="hash"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.get("/account/deposit")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--deposit-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

def test_deposit_post_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.post(
        "/account/deposit",
        data={"amount": 100},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_deposit_post_authorized_returns_200_and_renders_account(client, app, session):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="user",
        balance=Decimal("50"),
        auth=UserAuth(login="test_login", pwd_hash="hash"),
    )
    services.repository.user.add_user(user, session)
    session.commit()
    session.refresh(user)
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.post(
        "/account/deposit",
        data={"amount": 100},
        follow_redirects=False,
    )
    session.refresh(user)
    assert user.balance == Decimal("150")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--account-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

def test_account_transactions_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/account/transactions", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_account_transactions_authorized_returns_200(client, app):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="Test User",
        auth=UserAuth(login="login", pwd_hash="hash"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.get("/account/transactions")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--transactions-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)

