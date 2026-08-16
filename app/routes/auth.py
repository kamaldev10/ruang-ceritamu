"""Auth routes — login & register di satu halaman dengan tab."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from flask_mail import Message

from app.extensions import db, limiter, mail
from app.models import User, Role
from app.forms import LoginForm, RegisterForm, RequestResetForm, ResetPasswordForm
from app.utils import log_audit

auth_bp = Blueprint("auth", __name__)


def _send_or_log(msg, link):
    """Kirim email, atau kalau MAIL_SUPPRESS_SEND aktif (tidak ada SMTP di dev),
    catat link ke log supaya tetap bisa ditest manual."""
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        current_app.logger.info(f"[MAIL SUPPRESSED] To: {msg.recipients} | Link: {link}")
    mail.send(msg)


def send_reset_email(user):
    token = user.get_reset_token()
    link = url_for('auth.reset_token', token=token, _external=True)
    msg = Message('Permintaan Reset Kata Sandi - RuangCeritamu',
                  recipients=[user.email])
    msg.body = f'''Untuk me-reset kata sandi Anda, kunjungi tautan berikut:
{link}

Tautan ini berlaku 30 menit. Jika Anda tidak melakukan permintaan ini, abaikan email ini.
'''
    _send_or_log(msg, link)


def _redirect_by_role(user):
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if user.is_psikolog:
        return redirect(url_for("psikolog.dashboard"))
    return redirect(url_for("user.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    login_form = LoginForm(prefix="login")
    register_form = RegisterForm(prefix="register")

    if login_form.validate_on_submit() and request.form.get("form_type") == "login":
        email_input = login_form.email.data.strip()
        user = User.query.filter(
            (User.email == email_input) | (User.username == email_input)
        ).first()
        if user is None or not user.check_password(login_form.password.data):
            log_audit("login_failed", detail=f"Attempt for {email_input}")
            db.session.commit()
            flash("Email/username atau kata sandi salah.", "error")
            return render_template("auth/auth.html", login_form=login_form,
                                   register_form=register_form, active_tab="login")
        if not user.is_active_account:
            flash("Akun ditangguhkan. Hubungi admin.", "error")
            return render_template("auth/auth.html", login_form=login_form,
                                   register_form=register_form, active_tab="login")

        login_user(user, remember=login_form.remember_me.data)
        log_audit("login_success")
        db.session.commit()
        flash(f"Selamat datang, {user.username}!", "success")

        next_page = request.args.get("next")
        if next_page and urlparse(next_page).netloc == "":
            return redirect(next_page)
        return _redirect_by_role(user)

    return render_template("auth/auth.html", login_form=login_form,
                           register_form=register_form, active_tab="login")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    login_form = LoginForm(prefix="login")
    register_form = RegisterForm(prefix="register")

    if register_form.validate_on_submit() and request.form.get("form_type") == "register":
        user = User(
            username=register_form.username.data.strip(),
            email=register_form.email.data.lower().strip(),
            role=Role.USER.value,
        )
        user.set_password(register_form.password.data)
        db.session.add(user)
        db.session.flush()
        log_audit("user_registered", target_type="user", target_id=user.id, detail=user.email)
        db.session.commit()
        flash("Akun berhasil dibuat!", "success")
        login_user(user)
        return redirect(url_for("user.dashboard"))

    return render_template("auth/auth.html", login_form=login_form,
                           register_form=register_form, active_tab="register")


@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            send_reset_email(user)
        flash("Email instruksi reset kata sandi telah dikirim jika akun terdaftar.", "info")
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)
    user = User.verify_reset_token(token)
    if user is None:
        flash("Tautan tidak valid atau sudah kedaluwarsa.", "error")
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        log_audit("password_changed", target_type="user", target_id=user.id)
        db.session.commit()
        flash("Kata sandi berhasil diperbarui! Silakan masuk.", "success")
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_audit("logout")
    db.session.commit()
    logout_user()
    flash("Sampai jumpa lagi.", "info")
    return redirect(url_for("main.index"))
