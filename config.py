"""Konfigurasi multi-environment CeritaKita."""
import os
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool
from db import get_database_uri

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "ubah-secret-key-ini-di-production"
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "200/hour"

    # Origin yang boleh buka koneksi WebSocket (Flask-SocketIO). "*" cocok untuk
    # dev, tapi HARUS dipersempit ke domain asli di production (lihat
    # ProductionConfig). Boleh berupa satu origin, atau beberapa dipisah koma.
    _cors_env = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
    SOCKETIO_CORS_ALLOWED_ORIGINS = (
        [o.strip() for o in _cors_env.split(",")] if "," in _cors_env else _cors_env
    )

    # Mail Settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or "no-reply@ceritakita.id"
    # Tanpa MAIL_SERVER (mis. dev lokal tanpa SMTP), email tidak benar-benar dikirim —
    # link verifikasi/reset dicatat ke log lewat app.logger sebagai gantinya.
    MAIL_SUPPRESS_SEND = os.environ.get(
        "MAIL_SUPPRESS_SEND", "false" if os.environ.get("MAIL_SERVER") else "true"
    ).lower() == "true"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get("SECRET_KEY")  # WAJIB di-set di production


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # StaticPool + check_same_thread=False: satu koneksi SQLite in-memory yang
    # sama dipakai ulang untuk semua request test, supaya tabel yang dibuat di
    # awal test tidak "hilang" ketika SQLAlchemy membuka koneksi baru.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
