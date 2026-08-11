"""Admin routes — full control over platform."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from app.extensions import db
from app.models import (User, ChatSession, ForumPost, ForumComment, Report,
                        AuditLog, MoodLog, Message, Role, SessionStatus, MarqueeItem)
from app.forms import AdminCreatePsikologForm, MarqueeItemForm
from app.utils import role_required, time_ago, log_audit, send_notification

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    week_ago = datetime.utcnow() - timedelta(days=7)

    stats = {
        "chat_today": ChatSession.query.filter(ChatSession.started_at >= today_start).count(),
        "reports_active": Report.query.filter_by(status="pending").count(),
        "psikolog_total": User.query.filter_by(role=Role.PSIKOLOG.value).count(),
        "user_total": User.query.filter_by(role=Role.USER.value).count(),
        "active_sessions": ChatSession.query.filter_by(status=SessionStatus.ACTIVE.value).count(),
        "waiting_sessions": ChatSession.query.filter_by(status=SessionStatus.WAITING.value).count(),
        "crisis_sessions": ChatSession.query.filter_by(has_crisis_flag=True).filter(
            ChatSession.status.in_([SessionStatus.ACTIVE.value, SessionStatus.WAITING.value])).count(),
        "posts_today": ForumPost.query.filter(ForumPost.created_at >= today_start).count(),
        "sessions_week": ChatSession.query.filter(ChatSession.started_at >= week_ago).count(),
    }

    crisis_sessions = ChatSession.query.filter_by(has_crisis_flag=True).filter(
        ChatSession.status != SessionStatus.ENDED.value).order_by(desc(ChatSession.started_at)).limit(5).all()
    recent_reports = Report.query.filter_by(status="pending").order_by(desc(Report.created_at)).limit(5).all()
    recent_logs = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(8).all()

    return render_template("admin/dashboard.html", stats=stats, crisis_sessions=crisis_sessions,
                           recent_reports=recent_reports, recent_logs=recent_logs, time_ago=time_ago)


# ─── USER MANAGEMENT ───────────────────────────────────────────────
@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    role_filter = request.args.get("role", "")
    search = request.args.get("q", "").strip()
    q = User.query
    if role_filter in ("admin", "psikolog", "user"):
        q = q.filter_by(role=role_filter)
    if search:
        q = q.filter((User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    users_list = q.order_by(desc(User.created_at)).limit(100).all()
    return render_template("admin/users.html", users=users_list, role_filter=role_filter, search=search)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Tidak bisa nonaktifkan akun sendiri.", "error")
        return redirect(url_for("admin.users"))
    user.is_active_account = not user.is_active_account
    status = "diaktifkan" if user.is_active_account else "dinonaktifkan"
    log_audit(f"user_{status}", target_type="user", target_id=user.id, detail=user.username)
    db.session.commit()
    flash(f"Akun {user.username} {status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/change-role", methods=["POST"])
@login_required
@role_required("admin")
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("new_role")
    if new_role not in ("admin", "psikolog", "user"):
        abort(400)
    if user.id == current_user.id:
        flash("Tidak bisa ubah role sendiri.", "error")
        return redirect(url_for("admin.users"))
    old_role = user.role
    user.role = new_role
    log_audit("role_changed", target_type="user", target_id=user.id,
              detail=f"{user.username}: {old_role} -> {new_role}")
    db.session.commit()
    flash(f"Role {user.username} diubah ke {new_role}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/verify", methods=["POST"])
@login_required
@role_required("admin")
def verify_psikolog(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    status = "terverifikasi" if user.is_verified else "belum terverifikasi"
    log_audit(f"psikolog_{status}", target_type="user", target_id=user.id, detail=user.username)
    send_notification(user.id, "Status Verifikasi Diperbarui",
                      f"Akun kamu sekarang {status} oleh admin.", notif_type="info")
    db.session.commit()
    flash(f"{user.username} {status}.", "success")
    return redirect(url_for("admin.users", role="psikolog"))


@admin_bp.route("/psikolog/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def new_psikolog():
    form = AdminCreatePsikologForm()
    if form.validate_on_submit():
        p = User(username=form.username.data.strip(), email=form.email.data.lower().strip(),
                 full_name=form.full_name.data.strip(), bio=(form.bio.data or "").strip() or None,
                 role=Role.PSIKOLOG.value, must_change_password=True)
        p.set_password(form.password.data)
        db.session.add(p)
        log_audit("psikolog_created", target_type="user", detail=p.email)
        db.session.commit()
        flash(f"Akun psikolog {p.username} dibuat.", "success")
        return redirect(url_for("admin.users", role="psikolog"))
    return render_template("admin/new_psikolog.html", form=form)


# ─── SESSION MANAGEMENT ────────────────────────────────────────────
@admin_bp.route("/sessions")
@login_required
@role_required("admin")
def sessions():
    status_filter = request.args.get("status", "")
    crisis_only = request.args.get("crisis") == "1"
    q = ChatSession.query
    if status_filter in ("waiting", "active", "ended"):
        q = q.filter_by(status=status_filter)
    if crisis_only:
        q = q.filter_by(has_crisis_flag=True)
    sessions_list = q.order_by(desc(ChatSession.started_at)).limit(50).all()
    return render_template("admin/sessions.html", sessions=sessions_list,
                           status_filter=status_filter, crisis_only=crisis_only, time_ago=time_ago)


@admin_bp.route("/sessions/<code>/view")
@login_required
@role_required("admin")
def view_session(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    messages = Message.query.filter_by(session_id=sess.id).order_by(Message.sent_at.asc()).all()
    return render_template("admin/view_session.html", sess=sess, messages=messages, time_ago=time_ago)


@admin_bp.route("/sessions/<code>/end", methods=["POST"])
@login_required
@role_required("admin")
def admin_end_session(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    sess.status = SessionStatus.ENDED.value
    sess.ended_at = datetime.utcnow()
    log_audit("session_force_ended", target_type="session", target_id=sess.id, detail=code)
    db.session.commit()
    flash(f"Sesi {code} ditutup paksa.", "success")
    return redirect(url_for("admin.sessions"))


# ─── FORUM MODERATION ──────────────────────────────────────────────
@admin_bp.route("/forum")
@login_required
@role_required("admin")
def forum_mod():
    q = request.args.get("q", "").strip()
    show_hidden = request.args.get("hidden") == "1"
    query = ForumPost.query
    if show_hidden:
        query = query.filter_by(is_hidden=True)
    if q:
        query = query.filter(ForumPost.title.ilike(f"%{q}%"))
    posts = query.order_by(desc(ForumPost.created_at)).limit(50).all()
    return render_template("admin/forum_mod.html", posts=posts, search=q,
                           show_hidden=show_hidden, time_ago=time_ago)


@admin_bp.route("/forum/post/<int:post_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    post.is_hidden = not post.is_hidden
    action = "post_hidden" if post.is_hidden else "post_unhidden"
    log_audit(action, target_type="post", target_id=post.id, detail=post.title[:60])
    db.session.commit()
    flash(f"Post {'disembunyikan' if post.is_hidden else 'ditampilkan kembali'}.", "success")
    return redirect(url_for("admin.forum_mod"))


@admin_bp.route("/forum/comment/<int:cid>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_comment(cid):
    c = ForumComment.query.get_or_404(cid)
    c.is_hidden = not c.is_hidden
    log_audit("comment_toggled", target_type="comment", target_id=c.id)
    db.session.commit()
    flash("Komentar diperbarui.", "success")
    return redirect(url_for("admin.forum_mod"))


# ─── REPORTS ────────────────────────────────────────────────────────
@admin_bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    status = request.args.get("status", "pending")
    q = Report.query
    if status in ("pending", "resolved", "dismissed"):
        q = q.filter_by(status=status)
    reports_list = q.order_by(desc(Report.created_at)).limit(50).all()
    return render_template("admin/reports.html", reports=reports_list, status=status, time_ago=time_ago)


@admin_bp.route("/reports/<int:rid>/resolve", methods=["POST"])
@login_required
@role_required("admin")
def resolve_report(rid):
    report = Report.query.get_or_404(rid)
    action = request.form.get("action", "dismiss")
    report.status = "resolved" if action == "hide" else "dismissed"
    report.resolved_at = datetime.utcnow()
    report.resolved_by = current_user.id
    if action == "hide" and report.target_type == "post":
        post = ForumPost.query.get(report.target_id)
        if post:
            post.is_hidden = True
    log_audit(f"report_{report.status}", target_type="report", target_id=report.id)
    db.session.commit()
    flash("Laporan diproses.", "success")
    return redirect(url_for("admin.reports"))


# ─── LANDING PAGE — MARQUEE ─────────────────────────────────────────
@admin_bp.route("/marquee", methods=["GET", "POST"])
@login_required
@role_required("admin")
def marquee():
    form = MarqueeItemForm()
    if form.validate_on_submit():
        item = MarqueeItem(
            label=form.label.data.strip(),
            icon=(form.icon.data or "").strip() or "emergency_home",
            display_order=form.display_order.data or 0,
        )
        db.session.add(item)
        db.session.flush()
        log_audit("marquee_item_created", target_type="marquee_item", target_id=item.id, detail=item.label)
        db.session.commit()
        flash(f"Item '{item.label}' ditambahkan.", "success")
        return redirect(url_for("admin.marquee"))
    items = MarqueeItem.query.order_by(MarqueeItem.display_order.asc(), MarqueeItem.id.asc()).all()
    return render_template("admin/marquee.html", form=form, items=items)


@admin_bp.route("/marquee/<int:item_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_marquee(item_id):
    item = MarqueeItem.query.get_or_404(item_id)
    label = request.form.get("label", "").strip()
    icon = request.form.get("icon", "").strip()
    order_raw = request.form.get("display_order", "0").strip()
    if not label:
        flash("Teks tidak boleh kosong.", "error")
        return redirect(url_for("admin.marquee"))
    item.label = label
    item.icon = icon or "emergency_home"
    item.display_order = int(order_raw) if order_raw.isdigit() else 0
    log_audit("marquee_item_updated", target_type="marquee_item", target_id=item.id, detail=item.label)
    db.session.commit()
    flash(f"Item '{item.label}' diperbarui.", "success")
    return redirect(url_for("admin.marquee"))


@admin_bp.route("/marquee/<int:item_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_marquee(item_id):
    item = MarqueeItem.query.get_or_404(item_id)
    item.is_active = not item.is_active
    log_audit("marquee_item_toggled", target_type="marquee_item", target_id=item.id, detail=item.label)
    db.session.commit()
    flash(f"Item '{item.label}' {'diaktifkan' if item.is_active else 'dinonaktifkan'}.", "success")
    return redirect(url_for("admin.marquee"))


@admin_bp.route("/marquee/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_marquee(item_id):
    item = MarqueeItem.query.get_or_404(item_id)
    label = item.label
    log_audit("marquee_item_deleted", target_type="marquee_item", target_id=item.id, detail=label)
    db.session.delete(item)
    db.session.commit()
    flash(f"Item '{label}' dihapus.", "success")
    return redirect(url_for("admin.marquee"))


# ─── AUDIT LOGS ─────────────────────────────────────────────────────
@admin_bp.route("/logs")
@login_required
@role_required("admin")
def logs():
    page = request.args.get("page", 1, type=int)
    action_filter = request.args.get("action", "")
    q = AuditLog.query
    if action_filter:
        q = q.filter(AuditLog.action.ilike(f"%{action_filter}%"))
    pagination = q.order_by(desc(AuditLog.created_at)).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/logs.html", logs=pagination.items, pagination=pagination,
                           action_filter=action_filter, time_ago=time_ago)
