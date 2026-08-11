"""Mood tracker."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.extensions import db
from app.models import MoodLog
from app.forms import MoodForm
from app.utils import role_required, MOOD_EMOJI, MOOD_LABEL

mood_bp = Blueprint("mood", __name__)


@mood_bp.route("/", methods=["GET", "POST"])
@login_required
@role_required("user")
def tracker():
    form = MoodForm()
    if form.validate_on_submit():
        log = MoodLog(user_id=current_user.id, mood=form.mood.data,
                      note=(form.note.data or "").strip() or None)
        db.session.add(log)
        db.session.commit()
        flash("Mood tercatat.", "success")
        return redirect(url_for("mood.tracker"))

    week_ago = datetime.utcnow() - timedelta(days=7)
    logs = MoodLog.query.filter(MoodLog.user_id == current_user.id, MoodLog.created_at >= week_ago).order_by(MoodLog.created_at.asc()).all()
    history = MoodLog.query.filter_by(user_id=current_user.id).order_by(desc(MoodLog.created_at)).limit(30).all()
    mood_counts = {}
    for log in logs:
        mood_counts[log.mood] = mood_counts.get(log.mood, 0) + 1
    dominant_mood = max(mood_counts.items(), key=lambda x: x[1])[0] if mood_counts else None
    return render_template("mood/tracker.html", form=form, logs=logs, history=history,
                           dominant_mood=dominant_mood, MOOD_EMOJI=MOOD_EMOJI, MOOD_LABEL=MOOD_LABEL)
