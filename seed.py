"""
Seed script CeritaKita.
Jalankan: python seed.py
Database dibuat otomatis.
"""
from datetime import datetime, timedelta
from db import ensure_database_exists

ensure_database_exists()

from app import create_app, db
from app.models import (User, Role, ChatSession, SessionStatus,
                        ForumPost, ForumComment, MoodLog, MarqueeItem)


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Marquee landing page — dicek terpisah dari user supaya tetap ke-seed
        # walau user/psikolog/forum sudah ada (misal setelah migrasi model baru).
        if not MarqueeItem.query.first():
            for i, (label, icon) in enumerate([
                ("Konseling Anonim", "emergency_home"),
                ("Dukungan Emosional", "emergency_home"),
                ("Kesehatan Mental", "emergency_home"),
                ("Privasi Terjamin", "emergency_home"),
                ("Pembimbing Terlatih", "emergency_home"),
            ]):
                db.session.add(MarqueeItem(label=label, icon=icon, display_order=i))
            db.session.commit()
            print("🎗️  Marquee landing page di-seed.")

        if User.query.filter_by(email="admin@ceritakita.id").first():
            print("⚠️  Data seed sudah ada. Skip.")
            return

        print("🌱 Seeding...")

        # Admin
        admin = User(username="admin", email="admin@ceritakita.id",
                     full_name="Administrator", role=Role.ADMIN.value)
        admin.set_password("Admin123")
        db.session.add(admin)

        # Psikolog
        psi = []
        for u, e, fn, bio in [
            ("kak_sarah", "sarah@ceritakita.id", "Sarah Wijaya, S.Psi",
             "Pembimbing pendengar sejak 2023. Fokus kuliah & karier."),
            ("kak_andi", "andi@ceritakita.id", "Andi Prasetyo",
             "Peer counselor terlatih. Isu keluarga & pertemanan."),
            ("kak_maya", "maya@ceritakita.id", "Maya Putri",
             "Pendengar dengan latar psikologi remaja."),
        ]:
            p = User(username=u, email=e, full_name=fn, bio=bio,
                     role=Role.PSIKOLOG.value, must_change_password=True)
            p.set_password("Psikolog123")
            db.session.add(p)
            psi.append(p)

        # Users
        users = []
        for u, e in [("budi", "budi@example.com"), ("citra", "citra@example.com"),
                     ("rina", "rina@example.com")]:
            usr = User(username=u, email=e, role=Role.USER.value)
            usr.set_password("User1234")
            db.session.add(usr)
            users.append(usr)

        db.session.flush()

        # Forum
        posts_data = [
            ("Capek banget sama tugas kuliah",
             "Semua tugas numpuk dan aku ga tau harus mulai dari mana. Dosen kasih deadline berbarengan, aku nangis sendirian di kamar. Ada yang pernah ngerasain?",
             "Lelah", "AnakSenjaa", 7, users[0]),
            ("Putus sama pacar 3 tahun",
             "Udah 2 bulan tapi rasanya masih kayak baru kemarin. Setiap lihat foto lama jadi mewek. Aku tau harus move on tapi susah banget...",
             "Sedih", "Hujan", 12, users[1]),
            ("Hari ini aku berhasil bangun pagi",
             "Kedengeran sepele, tapi buat aku yang seminggu cuma tiduran di kasur, ini langkah besar. Pelan-pelan ya teman-teman.",
             "Self-Care", "Pagi", 23, users[2]),
            ("Overthinking soal masa depan",
             "Tiap malem ga bisa tidur mikirin kerjaan setelah lulus nanti. Padahal masih 2 tahun lagi. Gabisa stop mikir.",
             "Cemas", "MalamSunyi", 5, users[0]),
        ]
        for title, content, tag, pseudo, likes, user in posts_data:
            db.session.add(ForumPost(user_id=user.id, title=title, content=content,
                                     mood_tag=tag, pseudonym=pseudo, likes_count=likes))

        db.session.flush()
        first = ForumPost.query.first()
        if first:
            db.session.add(ForumComment(post_id=first.id, user_id=users[1].id,
                                        pseudonym="Teman",
                                        content="Aku juga lagi di posisi sama. Kita ga sendirian. 💚"))
            db.session.add(ForumComment(post_id=first.id, user_id=users[2].id,
                                        pseudonym="Pejuang",
                                        content="Coba teknik Pomodoro, 25 menit fokus 5 menit break."))

        # Mood logs
        moods = ["happy", "sad", "anxious", "neutral", "overthink", "happy", "sad"]
        notes = ["Lumayan oke", "Capek", "Mikirin ujian", "Biasa aja",
                 "Banyak pikiran", "Seru bareng temen", "Kangen rumah"]
        for i in range(7):
            db.session.add(MoodLog(user_id=users[0].id, mood=moods[i],
                                   note=notes[i],
                                   created_at=datetime.utcnow() - timedelta(days=i)))

        # Sample ended session
        db.session.add(ChatSession(
            session_code="CK-1001", user_id=users[0].id, psikolog_id=psi[0].id,
            topic="kuliah", status=SessionStatus.ENDED.value,
            started_at=datetime.utcnow() - timedelta(days=2),
            accepted_at=datetime.utcnow() - timedelta(days=2),
            ended_at=datetime.utcnow() - timedelta(days=2, hours=-1)))

        db.session.commit()

        print("✅ Seed selesai!\n")
        print("📝 Kredensial default:")
        print("   ┌────────────────────────────────────────────────┐")
        print("   │ ADMIN                                          │")
        print("   │   Email:    admin@ceritakita.id                │")
        print("   │   Password: Admin123                           │")
        print("   ├────────────────────────────────────────────────┤")
        print("   │ PSIKOLOG                                       │")
        print("   │   Email:    sarah@ceritakita.id (andi/maya)    │")
        print("   │   Password: Psikolog123                        │")
        print("   ├────────────────────────────────────────────────┤")
        print("   │ USER                                           │")
        print("   │   Email:    budi@example.com (citra/rina)      │")
        print("   │   Password: User1234                           │")
        print("   └────────────────────────────────────────────────┘")
        print("\n🚀 Jalankan: python run.py")


if __name__ == "__main__":
    seed()
