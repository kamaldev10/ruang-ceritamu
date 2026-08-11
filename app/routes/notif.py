"""Notification routes."""
from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.extensions import db
from app.models import Notification

notif_bp = Blueprint("notif", __name__)


@notif_bp.route("/")
@login_required
def index():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(desc(Notification.created_at)).limit(50).all()
    return render_template("notif/index.html", notifs=notifs)


@notif_bp.route("/read/<int:nid>")
@login_required
def read(nid):
    n = Notification.query.get_or_404(nid)
    if n.user_id != current_user.id:
        return "", 403
    n.is_read = True
    db.session.commit()
    if n.link:
        return redirect(n.link)
    return redirect(url_for("notif.index"))


@notif_bp.route("/read-all", methods=["POST"])
@login_required
def read_all():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("notif.index"))


@notif_bp.route("/count")
@login_required
def count():
    c = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"count": c})
