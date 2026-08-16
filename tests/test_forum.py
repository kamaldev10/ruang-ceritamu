from app.extensions import db
from app.models import ForumPost
from tests.conftest import login


def make_post(app, author):
    with app.app_context():
        post = ForumPost(user_id=author.id, title="Judul cerita", content="Isi cerita panjang" * 3)
        db.session.add(post)
        db.session.commit()
        return post.id


def test_report_post_notifies_all_admins(client, app, user, other_user, admin, make_user):
    second_admin = make_user("admin2", "admin2@ceritakita.id", role="admin")
    post_id = make_post(app, other_user)
    login(client, user.email)
    resp = client.post(f"/forum/post/{post_id}/report", data={"reason": "konten tidak pantas"},
                       follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert admin.unread_notif_count == 1
        assert second_admin.unread_notif_count == 1


def test_anonymous_cannot_report(client, app, other_user):
    post_id = make_post(app, other_user)
    resp = client.post(f"/forum/post/{post_id}/report", data={"reason": "spam"})
    assert resp.status_code in (302, 401)
