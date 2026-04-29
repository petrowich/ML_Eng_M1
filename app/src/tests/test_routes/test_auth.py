import services.repository.user
from auth.hash import create_hash
from models.user import User, UserAuth


def test_signup_returns_200(client):
    resp = client.get("/auth/signup")
    assert '<!--register-->' in resp.text
    assert resp.status_code == 200

def test_signup_creates_user_and_sets_cookie_and_redirects(client, session):
    login = f"login"
    email = f"test@test"
    password = "password"

    resp = client.post("/auth/signup",
        data={
            "login": login,
            "email": email,
            "password": password,
            "password_confirm": password,
        },
        follow_redirects=False,
    )

    assert resp.status_code == 303
    assert resp.headers.get("location") == "/"

    set_cookie = resp.headers.get("set-cookie", "")
    assert "ML_SERVICE_AUTH_TOKEN=" in set_cookie
    assert "HttpOnly" in set_cookie

    user = services.repository.user.get_user_by_login(login, session)

    assert user is not None
    assert user.email == "test@test"
    assert user.auth.login == "login"

def test_login_returns_200(client):
    resp = client.get("/auth/login")
    assert '<!--login-->' in resp.text
    assert resp.status_code == 200

def test_auth_login_success_redirects_and_sets_cookie(client, session):
    login = f"login"
    password = "password"
    email = f"user@example.test"

    pwd_hash = create_hash(password)
    user = User(email=email, auth=UserAuth(login=login, pwd_hash=pwd_hash))

    services.repository.user.add_user(user, session)

    resp = client.post(
        "/auth/login",
        data={"username": login, "password": password},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers.get("location") == "/"
    set_cookie = resp.headers.get("set-cookie", "")
    assert "ML_SERVICE_AUTH_TOKEN=" in set_cookie
    assert "HttpOnly" in set_cookie

def test_auth_login_invalid_password_returns_html_error(client, session):
    login = f"login"
    email = f"user@example.test"

    user = User(email=email, auth=UserAuth(login=login, pwd_hash=create_hash("CorrectPassword123!")))
    services.repository.user.add_user(user, session)

    resp = client.post(
        "/auth/login",
        data={"username": login, "password": "WrongPassword"},
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "set-cookie" not in resp.headers
    assert '<!--error-->' in resp.text
