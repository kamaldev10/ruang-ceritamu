"""Baseline (no-op) - adopting migrations on existing DB

Revision ID: 82d63c844155
Revises: 
Create Date: 2026-08-11 16:33:41.333164

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82d63c844155'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # No-op secara sengaja: revisi ini cuma menandai "mulai lacak dari sini",
    # bukan mengubah skema. Database live sudah punya semua tabel/kolom yang
    # dipakai app/models.py saat ini, dibuat manual (db.create_all() + ALTER
    # TABLE) sebelum Flask-Migrate dipakai di project ini.
    #
    # PENTING: autogenerate (`flask db migrate`) sempat mendeteksi 3 tabel
    # (`psikolog_credentials`, `forum_likes`, `session_ratings`) dan 3 kolom
    # di `users` (`locked_until`, `last_seen`, `login_attempts`) yang ADA di
    # DB tapi TIDAK ADA di app/models.py — sisa fitur dari sesi sebelumnya
    # yang modelnya hilang/tidak pernah di-commit (`forum_likes` bahkan
    # punya 1 baris data asli). Migrasi destruktif yang otomatis dibuat
    # (mau DROP semua itu) SENGAJA TIDAK dipakai — lihat memory project
    # untuk detail. Jangan generate ulang tanpa investigasi dulu.
    pass


def downgrade():
    pass
