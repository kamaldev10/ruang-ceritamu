"""User dashboard + settings."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, ChatSession, MoodLog, ForumPost, Role
from app.forms import EditProfileForm, ChangePasswordForm, DeleteAccountForm
from app.utils import role_required, MOOD_EMOJI, MOOD_LABEL, log_audit, save_upload

user_bp = Blueprint("user", __name__)


@user_bp.route("/dashboard")
@login_required
@role_required("user")
def dashboard():
    psikolog_online = User.query.filter_by(role=Role.PSIKOLOG.value, is_active_account=True).count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    moods_week = MoodLog.query.filter(MoodLog.user_id == current_user.id, MoodLog.created_at >= week_ago).order_by(MoodLog.created_at.asc()).all()
    recent_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.started_at.desc()).limit(5).all()
    recent_posts = ForumPost.query.filter_by(is_hidden=False).order_by(ForumPost.created_at.desc()).limit(3).all()
    return render_template("user/dashboard.html", psikolog_online=psikolog_online,
                           moods_week=moods_week, recent_sessions=recent_sessions,
                           recent_posts=recent_posts, MOOD_EMOJI=MOOD_EMOJI, MOOD_LABEL=MOOD_LABEL)


@user_bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("user")
def settings():
    profile_form = EditProfileForm(current_user.username, current_user.email, obj=current_user)
    password_form = ChangePasswordForm()
    delete_form = DeleteAccountForm()

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
            flash("Profil berhasil diperbarui.", "success")
            return redirect(url_for("user.settings"))

        elif action == "password" and password_form.validate_on_submit():
            if not current_user.check_password(password_form.current_password.data):
                flash("Password saat ini salah.", "error")
                return redirect(url_for("user.settings"))
            current_user.set_password(password_form.new_password.data)
            log_audit("password_changed", target_type="user", target_id=current_user.id)
            db.session.commit()
            flash("Password berhasil diubah.", "success")
            return redirect(url_for("user.settings"))

        elif action == "delete" and delete_form.validate_on_submit():
            uid = current_user.id
            log_audit("account_deleted", target_type="user", target_id=uid,
                      detail=current_user.username)
            current_user.is_active_account = False
            current_user.email = f"deleted_{uid}@removed.local"
            current_user.username = f"deleted_{uid}"
            current_user.full_name = None
            current_user.bio = None
            db.session.commit()
            from flask_login import logout_user
            logout_user()
            flash("Akunmu sudah dihapus. Data pribadi telah dianonimkan.", "info")
            return redirect(url_for("main.index"))

    return render_template("user/settings.html", profile_form=profile_form,
                           password_form=password_form, delete_form=delete_form)
