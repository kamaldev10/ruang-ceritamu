"""
Entry point CeritaKita.
Jalankan: python run.py
"""
# Monkey-patch HARUS paling awal, sebelum import lain (termasuk db driver) —
# supaya gevent bisa jalanin socket/threading standard library secara
# cooperative. Lihat dokumentasi Flask-SocketIO soal ini.
from gevent import monkey
monkey.patch_all()

from db import ensure_database_exists

ensure_database_exists()

from app import create_app, db
from app.extensions import socketio
from app.models import (User, ChatSession, Message, ForumPost,
                        ForumComment, MoodLog, Report, AuditLog)

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "ChatSession": ChatSession,
            "Message": Message, "ForumPost": ForumPost, "MoodLog": MoodLog,
            "Report": Report, "AuditLog": AuditLog}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tabel database siap.")
    print("\n🚀 Server (WebSocket aktif): http://localhost:5000\n   CTRL+C untuk stop.\n")
    # use_reloader=False: reloader Werkzeug (yang spawn subprocess) tidak
    # kompatibel baik dengan gevent yang sudah di-monkey-patch di process ini.
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
