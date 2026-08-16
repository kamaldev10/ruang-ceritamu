import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User, Role


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    """Factory: bikin & commit User dengan role tertentu, return objek User."""
    def _make(username, email, password="Password1", role=Role.USER.value, **kwargs):
        user = User(username=username, email=email, role=role, **kwargs)
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        return user
    return _make


@pytest.fixture()
def user(make_user):
    return make_user("budi", "budi@example.com", role=Role.USER.value)


@pytest.fixture()
def other_user(make_user):
    return make_user("citra", "citra@example.com", role=Role.USER.value)


@pytest.fixture()
def psikolog(make_user):
    return make_user("sarah", "sarah@ceritakita.id", role=Role.PSIKOLOG.value)


@pytest.fixture()
def other_psikolog(make_user):
    return make_user("andi", "andi@ceritakita.id", role=Role.PSIKOLOG.value)


@pytest.fixture()
def admin(make_user):
    return make_user("admin", "admin@ceritakita.id", role=Role.ADMIN.value)


def login(client, email, password="Password1"):
    return client.post("/auth/login", data={
        "form_type": "login",
        "login-email": email,
        "login-password": password,
    }, follow_redirects=True)
