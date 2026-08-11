"""Forum routes + pagination + notification on comment."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import desc
from app.extensions import db
from app.models import ForumPost, ForumComment, Report
from app.forms import ForumPostForm, CommentForm, ReportForm
from app.utils import time_ago, send_notification

forum_bp = Blueprint("forum", __name__)
PER_PAGE = 10


@forum_bp.route("/")
def feed():
    sort = request.args.get("sort", "latest")
    tag = request.args.get("tag")
    search = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    q = ForumPost.query.filter_by(is_hidden=False)
    if tag:
        q = q.filter(ForumPost.mood_tag == tag)
    if search:
        q = q.filter(ForumPost.title.ilike(f"%{search}%") | ForumPost.content.ilike(f"%{search}%"))
    if sort == "popular":
        q = q.order_by(desc(ForumPost.likes_count), desc(ForumPost.created_at))
    else:
        q = q.order_by(desc(ForumPost.created_at))
    pagination = q.paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("forum/feed.html", posts=pagination.items, pagination=pagination,
                           sort=sort, tag=tag, search=search, time_ago=time_ago)


@forum_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
def detail(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.is_hidden and not (current_user.is_authenticated and current_user.is_admin):
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Masuk dulu.", "info")
            return redirect(url_for("auth.login", next=request.url))
        comment = ForumComment(post_id=post.id, user_id=current_user.id,
                               content=form.content.data.strip(),
                               pseudonym=(form.pseudonym.data or "").strip() or None)
        db.session.add(comment)
        # Notif ke author post (kecuali kalau komentar sendiri)
        if post.user_id != current_user.id:
            send_notification(post.user_id, "Komentar baru",
                              f"Seseorang mengomentari ceritamu: \"{post.title[:50]}\"",
                              link=url_for("forum.detail", post_id=post.id),
                              notif_type="comment")
        db.session.commit()
        flash("Komentar terkirim.", "success")
        return redirect(url_for("forum.detail", post_id=post.id))
    comments = ForumComment.query.filter_by(post_id=post.id, is_hidden=False).order_by(ForumComment.created_at.asc()).all()
    return render_template("forum/detail.html", post=post, comments=comments, form=form, time_ago=time_ago)


@forum_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = ForumPostForm()
    if form.validate_on_submit():
        post = ForumPost(user_id=current_user.id, title=form.title.data.strip(),
                         content=form.content.data.strip(), mood_tag=form.mood_tag.data or None,
                         pseudonym=(form.pseudonym.data or "").strip() or None)
        db.session.add(post)
        db.session.commit()
        flash("Ceritamu sudah terbit.", "success")
        return redirect(url_for("forum.detail", post_id=post.id))
    return render_template("forum/new.html", form=form)


@forum_bp.route("/post/<int:post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()
    return {"likes_count": post.likes_count}


@forum_bp.route("/post/<int:post_id>/report", methods=["GET", "POST"])
@login_required
def report_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    form = ReportForm()
    if form.validate_on_submit():
        report = Report(reporter_id=current_user.id, target_type="post",
                        target_id=post.id, reason=form.reason.data.strip())
        db.session.add(report)
        db.session.commit()
        flash("Laporan terkirim.", "success")
        return redirect(url_for("forum.detail", post_id=post.id))
    return render_template("forum/report.html", form=form, post=post)
