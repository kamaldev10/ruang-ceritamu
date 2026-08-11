"""
Production WSGI entry point.

Gunicorn (Linux):
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

Waitress (Windows):
    waitress-serve --port=8000 wsgi:app
"""
import os
os.environ.setdefault("FLASK_ENV", "production")

from db import ensure_database_exists
ensure_database_exists()

from app import create_app, db

app = create_app("production")

with app.app_context():
    db.create_all()
