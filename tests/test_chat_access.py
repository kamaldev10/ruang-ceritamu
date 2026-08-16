from app.extensions import db
from app.models import ChatSession, SessionStatus
from tests.conftest import login


def make_session(app, owner, psikolog=None, status=SessionStatus.WAITING.value):
    with app.app_context():
        sess = ChatSession(session_code="CK-0001", user_id=owner.id,
                           psikolog_id=psikolog.id if psikolog else None, status=status)
        db.session.add(sess)
        db.session.commit()
        return sess.id


def test_owner_can_open_own_session(client, app, user):
    make_session(app, user)
    login(client, user.email)
    resp = client.get("/curhat/CK-0001")
    assert resp.status_code == 200


def test_other_user_cannot_open_someone_elses_session(client, app, user, other_user):
    make_session(app, user)
    login(client, other_user.email)
    resp = client.get("/curhat/CK-0001")
    assert resp.status_code == 403


def test_psikolog_opening_waiting_session_claims_it(client, app, user, psikolog):
    sid = make_session(app, user)
    login(client, psikolog.email)
    resp = client.get("/curhat/CK-0001")
    assert resp.status_code == 200
    with app.app_context():
        sess = db.session.get(ChatSession, sid)
        assert sess.status == SessionStatus.ACTIVE.value
        assert sess.psikolog_id == psikolog.id


def test_second_psikolog_cannot_join_active_session(client, app, user, psikolog, other_psikolog):
    make_session(app, user, psikolog=psikolog, status=SessionStatus.ACTIVE.value)
    login(client, other_psikolog.email)
    resp = client.get("/curhat/CK-0001")
    assert resp.status_code == 403


def test_ended_session_rejects_new_messages(client, app, user):
    make_session(app, user, status=SessionStatus.ENDED.value)
    login(client, user.email)
    resp = client.post("/curhat/CK-0001/send", data={"content": "halo"})
    assert resp.status_code == 400


def test_crisis_keyword_flags_session_and_notifies_admins(client, app, user, admin):
    make_session(app, user)
    login(client, user.email)
    resp = client.post("/curhat/CK-0001/send", data={"content": "aku pengen mati aja"})
    assert resp.status_code == 200
    assert resp.get_json()["is_crisis"] is True
    with app.app_context():
        sess = ChatSession.query.filter_by(session_code="CK-0001").first()
        assert sess.has_crisis_flag is True
        assert admin.unread_notif_count == 1
