"""
Konfigurasi database RuangCeritamu.

Baca kredensial dari .env (lihat .env.example). Kalau .env tidak ada atau
variabelnya tidak diset, fallback ke default Laragon (user 'root', password
kosong, port 3306) supaya tetap jalan out-of-the-box untuk dev lokal.
Database akan dibuat OTOMATIS kalau belum ada saat aplikasi pertama dijalankan.
"""
import os
import sys
from urllib.parse import quote_plus

import pymysql
from dotenv import load_dotenv

# Console Windows default-nya cp1252, yang tidak bisa encode emoji (✅/❌) di print
# bawah. Reconfigure ke UTF-8 di titik masuk paling awal supaya tidak crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# db.py bisa diimpor & dipakai (ensure_database_exists) SEBELUM config.py
# sempat load .env, jadi load di sini juga supaya urutan import tidak penting.
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


def _find_ca_bundle():
    custom_ca = os.environ.get("DB_SSL_CA")
    if custom_ca and os.path.exists(custom_ca):
        return custom_ca
    standard_paths = [
        "/etc/ssl/certs/ca-certificates.crt",  # Debian/Ubuntu/Render
        "/etc/pki/tls/certs/ca-bundle.crt",     # Fedora/CentOS/RHEL
        "/etc/ssl/ca-bundle.pem",               # OpenSUSE
        "/etc/ssl/cert.pem",                   # Alpine/macOS
    ]
    for p in standard_paths:
        if os.path.exists(p):
            return p
    return None


DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': os.environ.get('DB_NAME', 'db_cerita'),
    'ssl': (
        os.environ.get('DB_SSL', '').lower() in ('1', 'true', 'yes')
        or 'tidbcloud' in os.environ.get('DB_HOST', '').lower()
        or bool(os.environ.get('DB_SSL_CA'))
    ),
    'ssl_ca': _find_ca_bundle(),
}


def get_database_uri() -> str:
    """Build SQLAlchemy connection URI dari DB_CONFIG."""
    uri = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{quote_plus(DB_CONFIG['password'])}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )
    if DB_CONFIG.get('ssl'):
        if DB_CONFIG.get('ssl_ca'):
            uri += f"&ssl_ca={DB_CONFIG['ssl_ca']}"
        else:
            uri += "&ssl_verify_cert=true"
    return uri


def ensure_database_exists() -> None:
    """Bikin database kalau belum ada.

    Dipanggil sebelum app start supaya user tidak perlu manual CREATE DATABASE.
    Memerlukan MySQL server (Laragon/Cloud) sudah berjalan.
    """
    connect_kwargs = {
        'host': DB_CONFIG['host'],
        'user': DB_CONFIG['user'],
        'password': DB_CONFIG['password'],
        'port': DB_CONFIG['port'],
        'charset': 'utf8mb4',
    }
    if DB_CONFIG.get('ssl'):
        if DB_CONFIG.get('ssl_ca'):
            connect_kwargs['ssl'] = {'ca': DB_CONFIG['ssl_ca']}
        else:
            connect_kwargs['ssl'] = {'ssl_mode': 'REQUIRED'}

    # 1. Coba koneksi langsung ke database yang dituju
    try:
        conn = pymysql.connect(database=DB_CONFIG['database'], **connect_kwargs)
        conn.close()
        print(f"✅ Database '{DB_CONFIG['database']}' siap digunakan.")
        return
    except pymysql.MySQLError:
        # Lanjut ke langkah 2 jika database belum ada atau perlu dibuat
        pass

    # 2. Jika belum ada (mis. dev lokal/Laragon), coba buat database otomatis
    try:
        conn = pymysql.connect(**connect_kwargs)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
        finally:
            conn.close()
        print(f"✅ Database '{DB_CONFIG['database']}' berhasil dibuat/disiapkan.")
    except pymysql.MySQLError as e:
        print(f"⚠️  Catatan database: {e}")
        print(f"   Jika menggunakan Cloud Database (seperti TiDB Cloud), pastikan database '{DB_CONFIG['database']}' sudah dibuat di console/dashboard provider Anda (atau gunakan database default 'test').")

