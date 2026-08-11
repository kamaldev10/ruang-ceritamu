# CeritaKita 💚

Platform curhat anonim gratis untuk anak muda Indonesia. Flask + MySQL.

## 🎯 Fitur Lengkap

| Kategori | Fitur |
|----------|-------|
| **Chat** | 1:1 anonim, matchmaking acak (CK-XXXX), upload gambar, deteksi krisis |
| **Forum** | Cerita publik, tag mood, like, komentar, search, pagination |
| **Mood** | Tracker harian, insight mingguan |
| **Profil** | Edit profil + avatar, ubah password, hapus akun (UU PDP) |
| **Notifikasi** | Bell icon, real-time count, notif komentar/sesi/krisis |
| **Admin** | Sidebar, user management, verifikasi psikolog, sesi chat, forum moderasi, laporan, audit log |
| **Keamanan** | Password ketat (8+ char, huruf besar, angka), rate limiting, CSRF, audit trail |
| **Legal** | Privacy Policy (UU PDP), Terms of Service, halaman darurat |
| **Production** | Multi-env config, WSGI (Gunicorn/Waitress), logging, Flask-Migrate |

## 🚀 Quick Start

### 1. Jalankan Laragon & MySQL

Pastikan Laragon sudah berjalan dan MySQL aktif (port 3306).
Database `db_cerita` akan dibuat **otomatis** saat aplikasi pertama kali dijalankan.

> **Catatan Laragon:** Default user = `root`, password = kosong.
> Jika berbeda, edit file `db.py` pada bagian:
> ```python
> 'user': 'root',
> 'password': '',   # ganti jika perlu
> 'port': 3306,
> ```

### 2. Setup & Jalankan

```bash
cd ceritakita
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python run.py
```

Buka **http://localhost:5000**

### 3. Production (opsional)

```bash
pip install gunicorn     # Linux
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

pip install waitress     # Windows
waitress-serve --port=8000 wsgi:app
```

## 🔑 Kredensial Default

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@ceritakita.id` | `Admin123` |
| Psikolog | `sarah@ceritakita.id` / `andi` / `maya` | `Psikolog123` |
| User | `budi@example.com` / `citra` / `rina` | `User1234` |

## 🗂️ Struktur (80+ file)

```
ceritakita/
├── run.py / wsgi.py           # Dev & production entry points
├── db.py / config.py          # Database & multi-env config
├── seed.py                    # Data awal
└── app/
    ├── models.py              # 9 models (User, Chat, Forum, Mood, Report, AuditLog, Notification)
    ├── forms.py               # 12 forms (termasuk EditProfile, ChangePassword, DeleteAccount)
    ├── utils.py               # Crisis detection, file upload, notifications, audit
    ├── routes/
    │   ├── admin.py           # 13 endpoints (dashboard, users, sessions, forum, reports, logs, verify)
    │   ├── auth.py            # Combined login+register (rate limited)
    │   ├── chat.py            # Matchmaking + crisis + file upload
    │   ├── forum.py           # CRUD + search + pagination + comment notification
    │   ├── mood.py            # Tracker + insight
    │   ├── user.py            # Dashboard + settings (edit/password/delete)
    │   ├── psikolog.py        # Dashboard + settings
    │   ├── notif.py           # Notification list + read/read-all
    │   └── main.py            # Landing, about, emergency, privacy, tos
    └── templates/             # 30+ templates (sidebar dashboard layout)
```

## ⚠️ Checklist Improvement (20 item)

| # | Fitur | Status |
|---|-------|--------|
| 1 | Deteksi krisis (30+ keyword) + notif admin | ✅ |
| 2 | Verifikasi psikolog oleh admin | ✅ |
| 3 | Privacy Policy & Terms of Service | ✅ |
| 4 | Audit trail (AuditLog) | ✅ |
| 5 | Password ketat + rate limiting | ✅ |
| 6 | Forgot password (email) | ❌ Butuh SMTP |
| 7 | Email verification | ❌ Butuh SMTP |
| 8 | WebSocket chat | ❌ Masih polling |
| 9 | Edit profil + hapus akun | ✅ |
| 10 | Notifikasi (bell + badge) | ✅ |
| 11 | Pagination + search forum | ✅ |
| 12 | File upload chat (gambar) | ✅ |
| 13 | Smoke test suite | ✅ |
| 14 | Flask-Migrate ready | ✅ |
| 15 | Multi-env config | ✅ |
| 16 | WSGI production (wsgi.py) | ✅ |
| 17 | HTTPS config | ⚠️ Di ProductionConfig |
| 18 | Database backup | ❌ Manual mysqldump |
| 19 | Monitoring/Sentry | ❌ |
| 20 | Logo SVG + favicon | ✅ |

**Skor: 15/20 selesai.**

## ⚖️ Disclaimer

CeritaKita bukan terapi profesional. Untuk krisis: **119 ext. 8** · [intothelightid.org](https://www.intothelightid.org)

---
Dibangun dengan 💚 untuk anak muda Indonesia.
