"""SocketIO event handlers — real-time push untuk chat 1:1.

Aksi yang butuh proteksi CSRF/upload/audit (kirim pesan, akhiri sesi) tetap
lewat route REST biasa di app/routes/chat.py; socket cuma dipakai untuk
push instan (pesan baru, status mengetik, read receipt) supaya klien tidak
perlu polling tiap 2.5 detik lagi. Polling tetap ada sebagai fallback lambat
kalau koneksi socket putus.
"""
from datetime import datetime, timedelta

from flask_login import current_user
from flask_socketio import join_room, emit
from sqlalchemy import func

from app.extensions import socketio, db
from app.models import ChatSession, Message

TYPING_WINDOW_SECONDS = 4


def _get_authorized_session(code):
    """Return ChatSession kalau current_user berhak akses, else None."""
    if not current_user.is_authenticated:
        return None
    sess = ChatSession.query.filter_by(session_code=code).first()
    if sess is None:
        return None
    if current_user.is_user and sess.user_id != current_user.id:
        return None
    if current_user.is_psikolog and sess.psikolog_id and sess.psikolog_id != current_user.id:
        return None
    return sess


def _my_role():
    if current_user.is_user:
        return "user"
    if current_user.is_psikolog:
        return "psikolog"
    return None


@socketio.on("join")
def handle_join(data):
    code = (data or {}).get("code")
    sess = _get_authorized_session(code)
    if sess is None:
        return
    join_room(code)


@socketio.on("typing")
def handle_typing(data):
    code = (data or {}).get("code")
    sess = _get_authorized_session(code)
    role = _my_role()
    if sess is None or role is None:
        return
    until = datetime.utcnow() + timedelta(seconds=TYPING_WINDOW_SECONDS)
    if role == "user":
        sess.user_typing_until = until
    else:
        sess.psikolog_typing_until = until
    db.session.commit()
    emit("typing", {"role": role}, room=code, include_self=False)


@socketio.on("mark_read")
def handle_mark_read(data):
    code = (data or {}).get("code")
    sess = _get_authorized_session(code)
    my_role = _my_role()
    if sess is None or my_role is None:
        return

    unread = Message.query.filter(Message.session_id == sess.id,
                                  Message.sender_role != my_role, Message.is_read.is_(False))
    if unread.first() is None:
        return
    unread.update({Message.is_read: True}, synchronize_session=False)
    db.session.commit()

    read_up_to = db.session.query(func.max(Message.id)).filter(
        Message.session_id == sess.id, Message.sender_role == my_role, Message.is_read.is_(True)
    ).scalar() or 0
    emit("read_receipt", {"read_up_to": read_up_to}, room=code)
