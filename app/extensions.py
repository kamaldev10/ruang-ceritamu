"""Inisialisasi Flask extensions."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan masuk dulu untuk mengakses halaman ini."
login_manager.login_message_category = "info"
