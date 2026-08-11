"""Public routes."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models import User, ChatSession, ForumPost, Role, MarqueeItem

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        if current_user.is_psikolog:
            return redirect(url_for("psikolog.dashboard"))
        return redirect(url_for("user.dashboard"))
    stats = {
        "sessions_done": ChatSession.query.filter_by(status="ended").count(),
        "psikolog_count": User.query.filter_by(role=Role.PSIKOLOG.value).count(),
        "stories_count": ForumPost.query.filter_by(is_hidden=False).count(),
    }
    marquee_items = MarqueeItem.query.filter_by(is_active=True).order_by(
        MarqueeItem.display_order.asc(), MarqueeItem.id.asc()).all()
    return render_template("main/landing.html", stats=stats, marquee_items=marquee_items)


@main_bp.route("/tentang")
def about():
    return render_template("main/about.html")


@main_bp.route("/darurat")
def emergency():
    return render_template("main/emergency.html")


@main_bp.route("/privasi")
def privacy():
    return render_template("main/privacy.html")


@main_bp.route("/ketentuan")
def tos():
    return render_template("main/tos.html")
