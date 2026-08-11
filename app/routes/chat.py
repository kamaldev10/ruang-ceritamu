"""Chat routes + crisis detection + file upload."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import ChatSession, Message, SessionStatus
from app.forms import StartCurhatForm, MessageForm
from app.utils import (role_required, generate_session_code, check_crisis,
                        flag_crisis_session, save_upload, send_notification, day_label)

TYPING_WINDOW_SECONDS = 4

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/")
@login_required
@role_required("user")
def pilih():
    form = StartCurhatForm()
    return render_template("chat/pilih.html", form=form)


@chat_bp.route("/start", methods=["POST"])
@login_required
@role_required("user")
def start():
    form = StartCurhatForm()
    if not form.validate_on_submit():
        flash("Ada masalah. Coba lagi.", "error")
        return redirect(url_for("chat.pilih"))
    existing = ChatSession.query.filter(
        ChatSession.user_id == current_user.id,
        ChatSession.status.in_([SessionStatus.WAITING.value, SessionStatus.ACTIVE.value]),
    ).first()
    if existing:
        return redirect(url_for("chat.room", code=existing.session_code))
    for _ in range(10):
        code = generate_session_code()
        if not ChatSession.query.filter_by(session_code=code).first():
            break
    else:
        flash("Gagal membuat kode sesi.", "error")
        return redirect(url_for("chat.pilih"))
    sess = ChatSession(session_code=code, user_id=current_user.id,
                       topic=form.topic.data or None, status=SessionStatus.WAITING.value)
    db.session.add(sess)
    db.session.commit()
    return redirect(url_for("chat.room", code=code))


@chat_bp.route("/<code>")
@login_required
def room(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if current_user.is_user and sess.user_id != current_user.id:
        abort(403)
    if current_user.is_psikolog and sess.status == SessionStatus.WAITING.value:
        sess.psikolog_id = current_user.id
        sess.status = SessionStatus.ACTIVE.value
        sess.accepted_at = datetime.utcnow()
        db.session.commit()
    elif current_user.is_psikolog and sess.psikolog_id and sess.psikolog_id != current_user.id:
        abort(403)
    form = MessageForm()
    messages = sess.messages.order_by(Message.sent_at.asc()).all()
    return render_template("chat/room.html", sess=sess, form=form, messages=messages, day_label=day_label)


@chat_bp.route("/<code>/messages")
@login_required
def messages_api(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if current_user.is_user and sess.user_id != current_user.id:
        abort(403)
    if current_user.is_psikolog and sess.psikolog_id and sess.psikolog_id != current_user.id:
        abort(403)
    after_id = request.args.get("after_id", 0, type=int)
    my_role = "user" if current_user.is_user else ("psikolog" if current_user.is_psikolog else None)

    if my_role:
        # Lagi buka/poll halaman ini = pesan lawan bicara yang belum kebaca, dianggap sudah dibaca.
        unread = Message.query.filter(Message.session_id == sess.id,
                                      Message.sender_role != my_role, Message.is_read.is_(False))
        if unread.first() is not None:
            unread.update({Message.is_read: True}, synchronize_session=False)
            db.session.commit()

    msgs = Message.query.filter(Message.session_id == sess.id, Message.id > after_id).order_by(Message.sent_at.asc()).all()

    read_up_to = 0
    other_typing = False
    if my_role:
        read_up_to = db.session.query(func.max(Message.id)).filter(
            Message.session_id == sess.id, Message.sender_role == my_role, Message.is_read.is_(True)
        ).scalar() or 0
        now = datetime.utcnow()
        typing_field = sess.psikolog_typing_until if my_role == "user" else sess.user_typing_until
        other_typing = bool(typing_field and typing_field > now)

    return jsonify({
        "status": sess.status,
        "has_crisis": sess.has_crisis_flag,
        "read_up_to": read_up_to,
        "other_typing": other_typing,
        "messages": [{"id": m.id, "sender_role": m.sender_role, "content": m.content,
                       "sent_at": m.sent_at.strftime("%H:%M"), "date_label": day_label(m.sent_at),
                       "is_crisis": m.is_crisis, "is_read": m.is_read,
                       "image": f"/static/chat_uploads/{m.image_filename}" if m.image_filename else None}
                      for m in msgs],
    })


@chat_bp.route("/<code>/typing", methods=["POST"])
@login_required
def typing_ping(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if current_user.is_user and sess.user_id != current_user.id:
        abort(403)
    if current_user.is_psikolog and sess.psikolog_id and sess.psikolog_id != current_user.id:
        abort(403)
    if sess.status == SessionStatus.ENDED.value:
        return ("", 204)
    until = datetime.utcnow() + timedelta(seconds=TYPING_WINDOW_SECONDS)
    if current_user.is_user:
        sess.user_typing_until = until
    elif current_user.is_psikolog:
        sess.psikolog_typing_until = until
    db.session.commit()
    return ("", 204)


@chat_bp.route("/<code>/send", methods=["POST"])
@login_required
def send_message(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if current_user.is_user and sess.user_id != current_user.id:
        abort(403)
    if current_user.is_psikolog and sess.psikolog_id and sess.psikolog_id != current_user.id:
        abort(403)
    if sess.status == SessionStatus.ENDED.value:
        return jsonify({"error": "Sesi sudah ditutup."}), 400

    content = (request.form.get("content") or "").strip()
    image_file = request.files.get("image")
    image_filename = None

    if image_file and image_file.filename:
        image_filename = save_upload(image_file, "chat_uploads")

    if not content and not image_filename:
        return jsonify({"error": "Pesan kosong."}), 400
    if content and len(content) > 2000:
        return jsonify({"error": "Pesan terlalu panjang."}), 400

    role = "user" if current_user.is_user else "psikolog"
    is_crisis = check_crisis(content) if content else False

    msg = Message(session_id=sess.id, sender_id=current_user.id,
                  sender_role=role, content=content or "[gambar]",
                  image_filename=image_filename, is_crisis=is_crisis)
    db.session.add(msg)

    if is_crisis:
        flag_crisis_session(sess)

    if sess.status == SessionStatus.WAITING.value and current_user.is_psikolog:
        sess.status = SessionStatus.ACTIVE.value
        sess.psikolog_id = current_user.id
        sess.accepted_at = datetime.utcnow()

    # Pesan baru keluar = tanda "sedang mengetik" milikku sendiri sudah tidak relevan lagi.
    if current_user.is_user:
        sess.user_typing_until = None
    elif current_user.is_psikolog:
        sess.psikolog_typing_until = None

    db.session.commit()
    return jsonify({"id": msg.id, "sender_role": role, "content": msg.content,
                    "sent_at": msg.sent_at.strftime("%H:%M"), "date_label": day_label(msg.sent_at),
                    "is_crisis": is_crisis, "is_read": False,
                    "image": f"/static/chat_uploads/{image_filename}" if image_filename else None})


@chat_bp.route("/<code>/end", methods=["POST"])
@login_required
def end_session(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if current_user.id not in (sess.user_id, sess.psikolog_id) and not current_user.is_admin:
        abort(403)
    sess.status = SessionStatus.ENDED.value
    sess.ended_at = datetime.utcnow()

    # Notifikasi ke user/psikolog bahwa sesi berakhir
    if current_user.id == sess.user_id and sess.psikolog_id:
        send_notification(sess.psikolog_id, "Sesi berakhir",
                          f"User mengakhiri sesi #{sess.session_code}.", notif_type="session")
    elif current_user.id == sess.psikolog_id:
        send_notification(sess.user_id, "Sesi berakhir",
                          f"Pendengar mengakhiri sesi #{sess.session_code}.", notif_type="session")

    db.session.commit()
    flash("Sesi berakhir. Terima kasih.", "info")
    if current_user.is_psikolog:
        return redirect(url_for("psikolog.dashboard"))
    if current_user.is_admin:
        return redirect(url_for("admin.sessions"))
    return redirect(url_for("user.dashboard"))
