"""Database models CeritaKita."""
import os
from datetime import datetime
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

from app.extensions import db


class Role(str, Enum):
    ADMIN = "admin"
    PSIKOLOG = "psikolog"
    USER = "user"


class SessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.USER.value, index=True)
    full_name = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_active_account = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)  # Untuk psikolog: sudah terverifikasi admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions_as_user = db.relationship("ChatSession", foreign_keys="ChatSession.user_id", backref="user", lazy="dynamic")
    sessions_as_psikolog = db.relationship("ChatSession", foreign_keys="ChatSession.psikolog_id", backref="psikolog", lazy="dynamic")
    forum_posts = db.relationship("ForumPost", backref="author", lazy="dynamic")
    forum_comments = db.relationship("ForumComment", backref="author", lazy="dynamic")
    mood_logs = db.relationship("MoodLog", backref="user", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic",
                                     foreign_keys="Notification.user_id")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id, 'purpose': 'reset'})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expires_sec)
            if data.get('purpose') != 'reset':
                return None
        except Exception:
            return None
        return db.session.get(User, data['user_id'])

    @property
    def is_admin(self):
        return self.role == Role.ADMIN.value

    @property
    def is_psikolog(self):
        return self.role == Role.PSIKOLOG.value

    @property
    def is_user(self):
        return self.role == Role.USER.value

    @property
    def unread_notif_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    @property
    def display_avatar(self):
        if self.avatar_url:
            return self.avatar_url
        return None


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    psikolog_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    topic = db.Column(db.String(80), nullable=True)
    status = db.Column(db.String(20), default=SessionStatus.WAITING.value, index=True)
    has_crisis_flag = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    user_typing_until = db.Column(db.DateTime, nullable=True)
    psikolog_typing_until = db.Column(db.DateTime, nullable=True)
    messages = db.relationship("Message", backref="session", lazy="dynamic",
                               cascade="all, delete-orphan", order_by="Message.sent_at.asc()")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)  # Upload gambar
    is_crisis = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sender = db.relationship("User", foreign_keys=[sender_id])


class ForumPost(db.Model):
    __tablename__ = "forum_posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood_tag = db.Column(db.String(40), nullable=True, index=True)
    pseudonym = db.Column(db.String(80), nullable=True)
    is_hidden = db.Column(db.Boolean, default=False)
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    comments = db.relationship("ForumComment", backref="post", lazy="dynamic",
                               cascade="all, delete-orphan", order_by="ForumComment.created_at.asc()")


class ForumComment(db.Model):
    __tablename__ = "forum_comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("forum_posts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    pseudonym = db.Column(db.String(80), nullable=True)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MoodLog(db.Model):
    __tablename__ = "mood_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    mood = db.Column(db.String(40), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_type = db.Column(db.String(40), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reporter = db.relationship("User", foreign_keys=[reporter_id])


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship("User", foreign_keys=[user_id])


class MarqueeItem(db.Model):
    """Teks berjalan di landing page — dikelola admin."""
    __tablename__ = "marquee_items"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(80), nullable=False)
    icon = db.Column(db.String(60), nullable=False, default="emergency_home")
    display_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(255), nullable=True)
    notif_type = db.Column(db.String(40), default="info")  # info, crisis, comment, session
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
