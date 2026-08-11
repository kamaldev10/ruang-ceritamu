"""Psikolog routes + settings."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.extensions import db
from app.models import ChatSession, SessionStatus
from app.forms import EditProfileForm, ChangePasswordForm
from app.utils import role_required, time_ago, log_audit, save_upload

psikolog_bp = Blueprint("psikolog", __name__)


@psikolog_bp.route("/dashboard")
@login_required
@role_required("psikolog")
def dashboard():
    waiting = ChatSession.query.filter_by(status=SessionStatus.WAITING.value).order_by(ChatSession.started_at.asc()).all()
    active_mine = ChatSession.query.filter_by(psikolog_id=current_user.id, status=SessionStatus.ACTIVE.value).all()
    week_ago = datetime.utcnow() - timedelta(days=7)
    done_this_week = ChatSession.query.filter(ChatSession.psikolog_id == current_user.id, ChatSession.status == SessionStatus.ENDED.value, ChatSession.ended_at >= week_ago).count()
    total_done = ChatSession.query.filter_by(psikolog_id=current_user.id, status=SessionStatus.ENDED.value).count()
    history = ChatSession.query.filter_by(psikolog_id=current_user.id).filter(ChatSession.status == SessionStatus.ENDED.value).order_by(desc(ChatSession.ended_at)).limit(5).all()
    return render_template("psikolog/dashboard.html", waiting=waiting, active_mine=active_mine,
                           done_this_week=done_this_week, total_done=total_done, history=history, time_ago=time_ago)


@psikolog_bp.route("/take/<code>")
@login_required
@role_required("psikolog")
def take(code):
    sess = ChatSession.query.filter_by(session_code=code).first_or_404()
    if sess.status != SessionStatus.WAITING.value:
        flash("Sesi sudah diambil.", "info")
        return redirect(url_for("psikolog.dashboard"))
    sess.psikolog_id = current_user.id
    sess.status = SessionStatus.ACTIVE.value
    sess.accepted_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("chat.room", code=code))


@psikolog_bp.route("/profile")
@login_required
@role_required("psikolog")
def profile():
    total_done = ChatSession.query.filter_by(psikolog_id=current_user.id, status=SessionStatus.ENDED.value).count()
    return render_template("psikolog/profile.html", total_done=total_done)


@psikolog_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("psikolog")
def settings():
    profile_form = EditProfileForm(current_user.username, current_user.email, obj=current_user)
    password_form = ChangePasswordForm()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "profile" and profile_form.validate_on_submit():
            current_user.username = profile_form.username.data.strip()
            current_user.email = profile_form.email.data.lower().strip()
            current_user.full_name = (profile_form.full_name.data or "").strip() or None
            current_user.bio = (profile_form.bio.data or "").strip() or None
            if profile_form.avatar.data:
                fname = save_upload(profile_form.avatar.data, "avatars")
                if fname:
                    current_user.avatar_url = f"/static/avatars/{fname}"
            log_audit("profile_updated", target_type="user", target_id=current_user.id)
            db.session.commit()
            flash("Profil diperbarui.", "success")
            return redirect(url_for("psikolog.settings"))

        elif action == "password" and password_form.validate_on_submit():
            if not current_user.check_password(password_form.current_password.data):
                flash("Password saat ini salah.", "error")
                return redirect(url_for("psikolog.settings"))
            current_user.set_password(password_form.new_password.data)
            current_user.must_change_password = False
            log_audit("password_changed", target_type="user", target_id=current_user.id)
            db.session.commit()
            flash("Password diubah.", "success")
            return redirect(url_for("psikolog.settings"))

    return render_template("psikolog/settings.html", profile_form=profile_form,
                           password_form=password_form)
