from app.models import User, Role
from tests.conftest import login


def test_register_creates_user_and_logs_in(client, app):
    resp = client.post("/auth/register", data={
        "form_type": "register",
        "register-username": "newbie",
        "register-email": "newbie@example.com",
        "register-password": "Password1",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        u = User.query.filter_by(email="newbie@example.com").first()
        assert u is not None
        assert u.role == Role.USER.value
        assert u.check_password("Password1")


def test_register_rejects_weak_password(client, app):
    resp = client.post("/auth/register", data={
        "form_type": "register",
        "register-username": "weakpw",
        "register-email": "weakpw@example.com",
        "register-password": "alllowercase1",  # tidak ada huruf besar
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="weakpw@example.com").first() is None


def test_register_rejects_duplicate_email(client, user):
    resp = client.post("/auth/register", data={
        "form_type": "register",
        "register-username": "budi2",
        "register-email": user.email,
        "register-password": "Password1",
    }, follow_redirects=True)
    assert "sudah terdaftar".encode() in resp.data


def test_login_with_correct_password_succeeds(client, user):
    resp = login(client, user.email, "Password1")
    assert resp.status_code == 200
    assert b"Selamat datang" in resp.data


def test_login_with_wrong_password_fails(client, user):
    resp = login(client, user.email, "SalahBanget1")
    assert "salah".encode() in resp.data


def test_login_with_username_also_works(client, user):
    resp = client.post("/auth/login", data={
        "form_type": "login",
        "login-email": user.username,
        "login-password": "Password1",
    }, follow_redirects=True)
    assert b"Selamat datang" in resp.data


def test_suspended_account_cannot_login(client, make_user):
    make_user("suspended", "suspended@example.com", is_active_account=False)
    resp = client.post("/auth/login", data={
        "form_type": "login",
        "login-email": "suspended@example.com",
        "login-password": "Password1",
    }, follow_redirects=True)
    assert "ditangguhkan".encode() in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/u/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_user_cannot_access_psikolog_dashboard(client, user):
    login(client, user.email)
    resp = client.get("/psikolog/dashboard")
    assert resp.status_code == 403


def test_user_cannot_access_admin_dashboard(client, user):
    login(client, user.email)
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 403


def test_psikolog_can_access_own_dashboard(client, psikolog):
    login(client, psikolog.email)
    resp = client.get("/psikolog/dashboard")
    assert resp.status_code == 200
