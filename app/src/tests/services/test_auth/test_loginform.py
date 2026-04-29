import asyncio

from services.auth.loginform import LoginForm

class DummyForm(dict):
    pass

class TestRequest:
    def __init__(self, form_data: dict):
        self._form_data = DummyForm(form_data)

    async def form(self):
        return self._form_data


def run(coro):
    return asyncio.run(coro)


def test_load_data_sets_username_and_password():
    request = TestRequest({"username": "username", "password": "password"})
    form = LoginForm(request)
    run(form.load_data())
    assert form.username == "username"
    assert form.password == "password"
    assert form.errors == []

def test_load_data_missing_fields_sets_none():
    request = TestRequest({})
    form = LoginForm(request)
    run(form.load_data())
    assert form.username is None
    assert form.password is None

def test_is_valid_true_when_username_and_password_ok():
    request = TestRequest({})
    form = LoginForm(request)
    form.username = "abc"
    form.password = "p"
    ok = run(form.is_valid())
    assert ok is True
    assert form.errors == []

def test_is_valid_username_too_short():
    request = TestRequest({})
    form = LoginForm(request)
    form.username = "ab"
    form.password = "p"
    ok = run(form.is_valid())
    assert ok is False
    assert len(form.errors) == 1

def test_is_valid_username_too_long():
    request = TestRequest({})
    form = LoginForm(request)
    form.username = "a" * 51
    form.password = "p"
    ok = run(form.is_valid())
    assert ok is False
    assert len(form.errors) == 1

def test_is_valid_password_missing_none():
    request = TestRequest({})
    form = LoginForm(request)
    form.username = "abcd"
    form.password = None
    ok = run(form.is_valid())
    assert ok is False
    assert len(form.errors) == 1

def test_is_valid_password_empty_string():
    request = TestRequest({})
    form = LoginForm(request)
    form.username = "abcd"
    form.password = ""
    ok = run(form.is_valid())
    assert ok is False
    assert len(form.errors) == 1

def test_load_data_empty_password():
    request = TestRequest({"username": "ab", "password": ""})
    form = LoginForm(request)
    run(form.load_data())
    ok = run(form.is_valid())
    assert ok is False
    assert len(form.errors) == 2