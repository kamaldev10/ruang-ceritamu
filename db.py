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


DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': os.environ.get('DB_NAME', 'db_cerita'),
}


def get_database_uri() -> str:
    """Build SQLAlchemy connection URI dari DB_CONFIG."""
    return (
        f"mysql+pymysql://{DB_CONFIG['user']}:{quote_plus(DB_CONFIG['password'])}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset=utf8mb4"
    )


def ensure_database_exists() -> None:
    """Bikin database kalau belum ada.

    Dipanggil sebelum app start supaya user tidak perlu manual CREATE DATABASE.
    Memerlukan MySQL server (Laragon) sudah berjalan.
    """
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            charset='utf8mb4',
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()
        finally:
            conn.close()
        print(f"✅ Database '{DB_CONFIG['database']}' siap digunakan.")
    except pymysql.MySQLError as e:
        print()
        print("❌ Gagal terhubung ke MySQL.")
        print(f"   Error: {e}")
        print()
        print("   Periksa hal berikut:")
        print(f"   1. Laragon sudah jalan dan MySQL aktif di port {DB_CONFIG['port']}?")
        print(f"   2. Kredensial di .env (DB_USER/DB_PASSWORD) sudah benar?")
        print()
        raise
