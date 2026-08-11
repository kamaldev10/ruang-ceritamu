"""Flask application factory CeritaKita."""
import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from config import config_map, Config
from app.extensions import db, login_manager, csrf, migrate, limiter, mail


def create_app(config_name=None):
    app = Flask(__name__)
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(config_name, Config))

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    mail.init_app(app)

    _setup_logging(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.chat import chat_bp
    from app.routes.forum import forum_bp
    from app.routes.mood import mood_bp
    from app.routes.psikolog import psikolog_bp
    from app.routes.admin import admin_bp
    from app.routes.notif import notif_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/u")
    app.register_blueprint(chat_bp, url_prefix="/curhat")
    app.register_blueprint(forum_bp, url_prefix="/forum")
    app.register_blueprint(mood_bp, url_prefix="/mood")
    app.register_blueprint(psikolog_bp, url_prefix="/psikolog")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(notif_bp, url_prefix="/notif")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server Error: {e}")
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template("errors/403.html"), 429

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from flask_login import current_user
        notif_count = 0
        if current_user.is_authenticated:
            notif_count = current_user.unread_notif_count
        return {
            "current_year": datetime.now().year,
            "app_name": "CeritaKita",
            "notif_count": notif_count,
        }

    return app


def _setup_logging(app):
    if app.config.get("TESTING"):
        return
    if not os.path.exists("logs"):
        os.mkdir("logs")
    fh = RotatingFileHandler("logs/ceritakita.log", maxBytes=1_048_576, backupCount=10)
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
    fh.setLevel(logging.INFO)
    app.logger.addHandler(fh)
    app.logger.setLevel(logging.INFO)
    app.logger.info("CeritaKita startup")
