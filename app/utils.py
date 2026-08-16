"""Helper functions RuangCeritamu."""
import os
import random
import string
import uuid
from functools import wraps
from datetime import datetime, timedelta

from flask import abort, request, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename


def generate_session_code() -> str:
    digits = "".join(random.choices(string.digits, k=4))
    return f"CK-{digits}"


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def time_ago(dt) -> str:
    if dt is None:
        return "-"
    delta = datetime.utcnow() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "baru saja"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} menit lalu"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} jam lalu"
    days = hours // 24
    if days < 7:
        return f"{days} hari lalu"
    return dt.strftime("%d %b %Y")


_BULAN_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def day_label(dt) -> str:
    """Label pemisah tanggal ala WhatsApp: 'Hari ini' / 'Kemarin' / '5 Agu 2026'."""
    today = datetime.utcnow().date()
    d = dt.date()
    if d == today:
        return "Hari ini"
    if d == today - timedelta(days=1):
        return "Kemarin"
    return f"{d.day} {_BULAN_ID[d.month - 1]} {d.year}"


def log_audit(action, target_type=None, target_id=None, detail=None):
    from app.extensions import db
    from app.models import AuditLog
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action, target_type=target_type, target_id=target_id,
        detail=detail, ip_address=request.remote_addr if request else None,
    )
    db.session.add(log)


def send_notification(user_id, title, message=None, link=None, notif_type="info"):
    """Kirim notifikasi ke user."""
    from app.extensions import db
    from app.models import Notification
    notif = Notification(user_id=user_id, title=title, message=message,
                         link=link, notif_type=notif_type)
    db.session.add(notif)


# ─── FILE UPLOAD ────────────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_upload(file_storage, subfolder="uploads"):
    """Simpan file upload dengan nama acak. Return filename atau None."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None

    # Cek ukuran
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_IMAGE_SIZE:
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    random_name = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.root_path, "static", subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, random_name)
    file_storage.save(filepath)
    return random_name


# ─── CRISIS DETECTION ──────────────────────────────────────────────
CRISIS_KEYWORDS = [
    "bunuh diri", "mau mati", "ingin mati", "pengen mati", "pgn mati",
    "akhiri hidup", "ngakhirin hidup", "mengakhiri hidup",
    "gak mau hidup", "ga mau hidup", "tidak mau hidup",
    "lebih baik mati", "mending mati", "mending gw mati",
    "gantung diri", "loncat dari", "lompat dari",
    "overdosis", "minum obat banyak", "telan obat",
    "potong nadi", "iris tangan", "sayat tangan",
    "self harm", "self-harm", "melukai diri",
    "tidak ada harapan", "gak ada harapan", "ga ada harapan",
    "dunia tanpa aku", "lebih baik tanpa aku",
]


def check_crisis(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in CRISIS_KEYWORDS)


def flag_crisis_session(session_obj):
    if not session_obj.has_crisis_flag:
        session_obj.has_crisis_flag = True
        log_audit("crisis_detected", target_type="session", target_id=session_obj.id,
                  detail=f"Crisis keyword di sesi {session_obj.session_code}")
        current_app.logger.warning(f"⚠️ CRISIS: session={session_obj.session_code}")

        # Kirim notifikasi ke semua admin
        from app.models import User, Role
        admins = User.query.filter_by(role=Role.ADMIN.value).all()
        for admin in admins:
            send_notification(admin.id, "⚠️ Krisis Terdeteksi",
                              f"Sesi {session_obj.session_code} mengandung keyword krisis.",
                              link=f"/admin/sessions/{session_obj.session_code}/view",
                              notif_type="crisis")


MOOD_EMOJI = {"happy": "😊", "neutral": "😐", "sad": "😭", "anxious": "😰", "overthink": "🌀"}
MOOD_LABEL = {"happy": "Senang", "neutral": "Biasa Saja", "sad": "Sedih", "anxious": "Cemas", "overthink": "Overthinking"}
