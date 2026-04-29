from models.user import User, UserAuth

def test_ml_tasks_unauthorized_redirects_to_login(client, app):
    from auth.oauth2 import get_current_user
    app.dependency_overrides[get_current_user] = lambda: None
    resp = client.get("/ml_tasks/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/auth/login/"
    app.dependency_overrides.pop(get_current_user, None)

def test_ml_tasks_authorized_returns_200(client, app):
    from auth.oauth2 import get_current_user
    user = User(
        email="user@example.test",
        name="Test User",
        auth=UserAuth(login="login", pwd_hash="hash"),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = client.get("/ml_tasks/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<!--ml_tasks-->" in resp.text
    app.dependency_overrides.pop(get_current_user, None)
