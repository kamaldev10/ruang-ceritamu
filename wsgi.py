"""
Production WSGI entry point.

Gunicorn + gevent worker (Linux) — DIPERLUKAN untuk WebSocket sungguhan
(worker sync/default gunicorn TIDAK support WebSocket upgrade):
    gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:8000 wsgi:app

Waitress (Windows):
    waitress-serve --port=8000 wsgi:app
    ⚠️ Waitress TIDAK support WebSocket. Chat tetap jalan (Socket.IO client
    otomatis fallback ke long-polling), tapi tidak dapat manfaat penuh
    real-time WebSocket. Untuk WebSocket sungguhan di Windows, jalankan
    lewat `python run.py` (pakai gevent's built-in server) alih-alih waitress.
"""
import os
os.environ.setdefault("FLASK_ENV", "production")

# Monkey-patch HARUS paling awal — lihat catatan yang sama di run.py.
from gevent import monkey
monkey.patch_all()

from db import ensure_database_exists
ensure_database_exists()

from app import create_app, db

app = create_app("production")

with app.app_context():
    db.create_all()
