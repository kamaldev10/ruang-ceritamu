# DESIGN.md — CeritaKita Technical Design Document

> Dokumen ini menjelaskan arsitektur, desain sistem, skema database, user flow, design system visual, dan keputusan teknis aplikasi CeritaKita secara menyeluruh.

---

## 1. Ringkasan Proyek

**CeritaKita** adalah platform peer-support (dukungan sebaya) berbasis web yang menyediakan ruang curhat anonim gratis untuk anak muda Indonesia. Platform ini menghubungkan user yang membutuhkan tempat bercerita dengan pembimbing pendengar terlatih melalui chat 1:1 anonim, forum cerita publik, dan mood tracker harian.

**Penegasan penting:** CeritaKita **bukan layanan terapi profesional**. Pendengar adalah pembimbing terlatih dasar, bukan psikolog/psikiater berlisensi. Untuk krisis serius, platform mengarahkan user ke hotline resmi (119 ext. 8).

### 1.1 Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Database | MySQL 8.0 (via Laragon / standalone) |
| ORM | Flask-SQLAlchemy |
| Migration | Flask-Migrate (Alembic) |
| Auth | Flask-Login, Werkzeug (password hashing) |
| Forms | Flask-WTF, WTForms |
| CSRF | Flask-WTF CSRFProtect |
| Rate Limiting | Flask-Limiter |
| Frontend | Jinja2 templates, Tailwind CSS (CDN), Material Symbols |
| Fonts | Be Vietnam Pro (heading), Inter (body) |
| Animation | AOS (Animate On Scroll) di landing page |
| Chat | WebSocket (Flask-SocketIO + gevent), polling 15 detik sbg fallback |
| Production | Gunicorn (Linux) / Waitress (Windows) via wsgi.py |

### 1.2 File Count & Structure

Total **78 file**, terdiri dari 20 file Python (~1.370 baris kode backend), 30+ template HTML, dan file konfigurasi/asset.

---

## 2. Arsitektur Aplikasi

### 2.1 High-Level Architecture

```
┌─────────────┐     HTTP      ┌──────────────────────────────┐
│   Browser    │ ◄──────────► │      Flask Application       │
│  (Tailwind   │              │                              │
│   + JS)      │              │  ┌──────────┐ ┌───────────┐  │
└─────────────┘              │  │  Routes   │ │ Templates │  │
                              │  │ (9 BP)   │ │ (Jinja2)  │  │
                              │  └────┬─────┘ └───────────┘  │
                              │       │                      │
                              │  ┌────▼─────┐                │
                              │  │  Models  │                │
                              │  │(SQLAlch) │                │
                              │  └────┬─────┘                │
                              │       │                      │
                              └───────┼──────────────────────┘
                                      │
                              ┌───────▼──────────┐
                              │   MySQL (db.py)   │
                              │   db_cerita       │
                              │   Auto-created    │
                              └──────────────────┘
```

### 2.2 Application Factory Pattern

File `app/__init__.py` menggunakan Flask Application Factory:

```
create_app(config_name)
├── Load config (Dev / Prod / Test)
├── Init extensions (db, login, csrf, migrate, limiter)
├── Setup logging (RotatingFileHandler -> logs/ceritakita.log)
├── Register 9 blueprints
├── Register error handlers (404, 500, 403, 429)
└── Context processor (current_year, app_name, notif_count)
```

### 2.3 Blueprint Organization

| Blueprint | Prefix | Fungsi | Endpoints |
|-----------|--------|--------|-----------|
| `main_bp` | `/` | Landing, about, darurat, privasi, ketentuan | 5 |
| `auth_bp` | `/auth` | Login, register, logout (rate limited) | 3 |
| `user_bp` | `/u` | Dashboard user, settings (edit/pw/delete) | 2 |
| `chat_bp` | `/curhat` | Pilih, start, room, messages API, send, end | 6 |
| `forum_bp` | `/forum` | Feed, detail, new, like, report | 5 |
| `mood_bp` | `/mood` | Tracker + insight | 1 |
| `psikolog_bp` | `/psikolog` | Dashboard, take, profile, settings | 4 |
| `admin_bp` | `/admin` | Dashboard, users, sessions, forum, reports, logs, verify | 13 |
| `notif_bp` | `/notif` | List, read, read-all, count (JSON) | 4 |
| | | **Total endpoints** | **43** |

---

## 3. Database Schema

### 3.1 Entity-Relationship Overview

```
users ──────────┬──── chat_sessions ──── messages
  │              │          │
  │              │          └── image_filename (upload)
  │              │
  ├── forum_posts ──── forum_comments
  │
  ├── mood_logs
  │
  ├── reports
  │
  ├── audit_logs
  │
  └── notifications
```

### 3.2 Tabel Detail

#### `users` — Semua tipe pengguna (admin, psikolog, user)

| Kolom | Tipe | Constraint | Keterangan |
|-------|------|-----------|------------|
| `id` | INT | PK, AUTO_INCREMENT | |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL, INDEX | Nama samaran |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL, INDEX | |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug scrypt hash |
| `role` | VARCHAR(20) | NOT NULL, INDEX | `admin` / `psikolog` / `user` |
| `full_name` | VARCHAR(120) | NULLABLE | Nama lengkap (opsional) |
| `bio` | TEXT | NULLABLE | Bio singkat |
| `avatar_url` | VARCHAR(255) | NULLABLE | Path ke file avatar upload |
| `is_active_account` | BOOLEAN | DEFAULT TRUE | False = akun di-ban/dihapus |
| `must_change_password` | BOOLEAN | DEFAULT FALSE | True untuk psikolog baru |
| `is_verified` | BOOLEAN | DEFAULT FALSE | Verifikasi admin untuk psikolog |
| `created_at` | DATETIME | DEFAULT UTC_NOW | |
| `updated_at` | DATETIME | AUTO UPDATE | |

**Relationships:**
- `sessions_as_user` -> ChatSession (FK user_id)
- `sessions_as_psikolog` -> ChatSession (FK psikolog_id)
- `forum_posts` -> ForumPost
- `forum_comments` -> ForumComment
- `mood_logs` -> MoodLog
- `notifications` -> Notification

**Properties:**
- `is_admin`, `is_psikolog`, `is_user` — role check
- `unread_notif_count` — live query count
- `display_avatar` — return avatar_url or None

#### `chat_sessions` — Sesi curhat 1:1

| Kolom | Tipe | Constraint | Keterangan |
|-------|------|-----------|------------|
| `id` | INT | PK | |
| `session_code` | VARCHAR(20) | UNIQUE, INDEX | Format: `CK-XXXX` (4 digit acak) |
| `user_id` | INT | FK -> users.id, NOT NULL | Pemilik sesi |
| `psikolog_id` | INT | FK -> users.id, NULLABLE | Null saat status waiting |
| `topic` | VARCHAR(80) | NULLABLE | kuliah/karir/keluarga/dll |
| `status` | VARCHAR(20) | INDEX | `waiting` -> `active` -> `ended` |
| `has_crisis_flag` | BOOLEAN | DEFAULT FALSE | True jika keyword krisis terdeteksi |
| `started_at` | DATETIME | DEFAULT UTC_NOW | |
| `accepted_at` | DATETIME | NULLABLE | Saat psikolog join |
| `ended_at` | DATETIME | NULLABLE | Saat sesi ditutup |

**Status flow:** `waiting` (user buat sesi) -> `active` (psikolog terima) -> `ended` (salah satu pihak akhiri)

#### `messages` — Pesan chat per sesi

| Kolom | Tipe | Constraint | Keterangan |
|-------|------|-----------|------------|
| `id` | INT | PK | Dipakai sebagai cursor polling (`after_id`) |
| `session_id` | INT | FK -> chat_sessions.id, INDEX | |
| `sender_id` | INT | FK -> users.id | |
| `sender_role` | VARCHAR(20) | | `user` atau `psikolog` |
| `content` | TEXT | NOT NULL | Isi pesan teks, atau `[gambar]` jika upload |
| `image_filename` | VARCHAR(255) | NULLABLE | UUID filename di `/static/chat_uploads/` |
| `is_crisis` | BOOLEAN | DEFAULT FALSE | True jika mengandung keyword krisis |
| `sent_at` | DATETIME | INDEX | Untuk ordering & display waktu |

#### `forum_posts` — Cerita di forum publik

| Kolom | Tipe | Constraint | Keterangan |
|-------|------|-----------|------------|
| `id` | INT | PK | |
| `user_id` | INT | FK -> users.id | Author |
| `title` | VARCHAR(200) | NOT NULL | |
| `content` | TEXT | NOT NULL | Min 20 karakter |
| `mood_tag` | VARCHAR(40) | INDEX | Lelah/Cemas/Sedih/Marah/Bingung/Syukur/Self-Care/Refleksi |
| `pseudonym` | VARCHAR(80) | NULLABLE | Nama samaran per-post |
| `is_hidden` | BOOLEAN | DEFAULT FALSE | True = disembunyikan admin |
| `likes_count` | INT | DEFAULT 0 | Counter denormalisasi |
| `created_at` | DATETIME | INDEX | |

#### `forum_comments`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INT | PK |
| `post_id` | INT | FK -> forum_posts.id, INDEX |
| `user_id` | INT | FK -> users.id |
| `content` | TEXT | |
| `pseudonym` | VARCHAR(80) | |
| `is_hidden` | BOOLEAN | Moderasi admin |
| `created_at` | DATETIME | |

#### `mood_logs`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INT | PK |
| `user_id` | INT | FK, INDEX |
| `mood` | VARCHAR(40) | `happy`/`neutral`/`sad`/`anxious`/`overthink` |
| `note` | TEXT | Catatan singkat (opsional) |
| `created_at` | DATETIME | INDEX |

#### `reports`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INT | PK |
| `reporter_id` | INT | FK -> users.id |
| `target_type` | VARCHAR(40) | `post` / `comment` / `session` / `user` |
| `target_id` | INT | ID dari target |
| `reason` | TEXT | Alasan laporan |
| `status` | VARCHAR(20) | `pending` -> `resolved` / `dismissed` |
| `created_at` | DATETIME | |
| `resolved_at` | DATETIME | |
| `resolved_by` | INT | FK -> users.id (admin yang resolve) |

#### `audit_logs`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INT | PK |
| `user_id` | INT | FK, NULLABLE (system events) |
| `action` | VARCHAR(100) | INDEX — misal: `login_success`, `crisis_detected`, `post_hidden` |
| `target_type` | VARCHAR(50) | `user` / `session` / `post` / `report` |
| `target_id` | INT | |
| `detail` | TEXT | Keterangan tambahan |
| `ip_address` | VARCHAR(50) | IP address pelaku |
| `created_at` | DATETIME | INDEX |

**Aksi yang di-log:** `login_success`, `login_failed`, `logout`, `user_registered`, `profile_updated`, `password_changed`, `account_deleted`, `crisis_detected`, `session_force_ended`, `post_hidden`, `post_unhidden`, `comment_toggled`, `report_resolved`, `report_dismissed`, `psikolog_created`, `user_diaktifkan`, `user_dinonaktifkan`, `role_changed`, `psikolog_terverifikasi`, `psikolog_belum terverifikasi`

#### `notifications`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INT | PK |
| `user_id` | INT | FK, INDEX — penerima |
| `title` | VARCHAR(200) | Judul notifikasi |
| `message` | TEXT | Detail (opsional) |
| `link` | VARCHAR(255) | URL tujuan saat diklik |
| `notif_type` | VARCHAR(40) | `info` / `crisis` / `comment` / `session` |
| `is_read` | BOOLEAN | INDEX |
| `created_at` | DATETIME | INDEX |

**Trigger notifikasi otomatis:**
- Komentar baru di post user -> notif ke author post (`comment`)
- Sesi diakhiri oleh salah satu pihak -> notif ke pihak lain (`session`)
- Keyword krisis terdeteksi -> notif ke semua admin (`crisis`)
- Admin verify/unverify psikolog -> notif ke psikolog (`info`)

---

## 4. Sistem Autentikasi & Keamanan

### 4.1 Password Policy

- Minimal 8 karakter
- Wajib mengandung minimal 1 huruf besar (A-Z)
- Wajib mengandung minimal 1 angka (0-9)
- Validasi di level form (`RegisterForm`, `ChangePasswordForm`) menggunakan regex
- Hash menggunakan Werkzeug `generate_password_hash` (scrypt by default)

### 4.2 Rate Limiting

| Endpoint | Limit | Tujuan |
|----------|-------|--------|
| `/auth/login` | 10 per menit | Cegah brute force |
| `/auth/register` | 5 per menit | Cegah spam akun |
| Global default | 200 per jam | General protection |

Menggunakan Flask-Limiter dengan `memory://` storage (untuk production, ganti ke Redis).

### 4.3 Role-Based Access Control

```
              ┌─────────┐
              │  Admin   │ ── Semua akses + kelola platform
              └─────────┘
                   │
              ┌─────────┐
              │Psikolog  │ ── Dashboard, terima sesi, chat, profil, settings
              └─────────┘
                   │
              ┌─────────┐
              │  User    │ ── Dashboard, curhat, forum, mood, settings
              └─────────┘
                   │
              ┌─────────┐
              │  Guest   │ ── Landing, forum (read-only), about, darurat
              └─────────┘
```

Decorator `@role_required('admin')` dipakai di route untuk enforce access.

### 4.4 CSRF Protection

- Semua form HTML menggunakan `{{ form.hidden_tag() }}` atau `{{ csrf_token() }}`
- AJAX requests menyertakan CSRF token di header `X-CSRFToken` atau form body
- `WTF_CSRF_TIME_LIMIT = 3600` (1 jam)

### 4.5 Session & Cookie Security

| Setting | Dev | Production |
|---------|-----|-----------|
| `SESSION_COOKIE_HTTPONLY` | True | True |
| `SESSION_COOKIE_SAMESITE` | Lax | Lax |
| `SESSION_COOKIE_SECURE` | — | True |
| `DEBUG` | True | False |

---

## 5. Fitur: Deteksi Keyword Krisis

### 5.1 Mekanisme

```
User mengirim pesan
        │
        ▼
check_crisis(content) — cek 30+ keyword Bahasa Indonesia
        │
    ┌───┴───┐
    │ True  │
    │       ▼
    │  flag_crisis_session()
    │       │
    │       ├── session.has_crisis_flag = True
    │       ├── AuditLog entry "crisis_detected"
    │       ├── Logger WARNING
    │       └── Notification -> semua admin
    │
    │  Di frontend:
    │       ├── Pesan ditandai ring-2 ring-error
    │       ├── Banner darurat muncul (hotline 119)
    │       └── Psikolog lihat alert merah di dashboard
    │
    └───┐
        │ False -> normal flow
        ▼
```

### 5.2 Daftar Keyword (30+ term)

Kategori yang di-cover: bunuh diri, keinginan mati, gantung diri, lompat dari ketinggian, overdosis, self-harm (potong/iris/sayat), keputusasaan total. Semua dalam Bahasa Indonesia informal/gaul.

### 5.3 Limitasi

- Hanya exact substring match (case-insensitive), bukan NLP/sentiment analysis
- Bisa false positive ("film bunuh diri") dan false negative (kode/singkatan yang belum di-list)
- Bukan pengganti intervensi manusia — hanya safety net

---

## 6. Fitur: Chat Anonim 1:1

### 6.1 User Flow

```
User                          System                        Psikolog
  │                              │                              │
  ├─ Klik "Mulai Curhat" ──────►│                              │
  ├─ Pilih topik (opsional) ───►│                              │
  ├─ Submit ───────────────────►│── Generate CK-XXXX           │
  │                              │── ChatSession(waiting)       │
  │◄─ Redirect ke /curhat/CK-XX │                              │
  │  [Banner: mencari...]        │                              │
  │                              │  ┌──────────────────────┐    │
  │                              │  │ Dashboard Psikolog   │    │
  │                              │  │ Antrean: CK-XXXX     │───►│
  │                              │  │ [Tombol: Terima]     │    │
  │                              │  └──────────────────────┘    │
  │                              │                              │
  │                              │◄── Psikolog klik "Terima" ──┤
  │                              │── status -> active            │
  │                              │── psikolog_id assigned       │
  │◄─ Polling: status=active     │──────────────────────────────│
  │  [Banner hilang]             │                              │
  │                              │                              │
  │── Kirim pesan ──────────────►│── Simpan Message ──────────►│
  │                              │                     polling  │
  │◄─────── polling ◄───────────│◄── Kirim pesan ─────────────┤
  │                              │                              │
  │── Upload gambar ────────────►│── save_upload() -> UUID.jpg  │
  │                              │── Message(image_filename)    │
  │                              │                              │
  │── "Akhiri Sesi" ───────────►│── status -> ended             │
  │                              │── Notif -> psikolog           │
```

### 6.2 Polling Mechanism

- Client-side: `setInterval(poll, 2500)` — setiap 2.5 detik
- Request: `GET /curhat/{code}/messages?after_id={last_id}`
- Response: `{ status, has_crisis, read_up_to, other_typing, messages: [{id, sender_role, content, sent_at, date_label, is_crisis, is_read, image}] }`
- Cursor-based: hanya ambil pesan dengan `id > after_id`, bukan seluruh riwayat
- Setiap poll juga menandai pesan dari lawan bicara yang belum `is_read` sebagai sudah dibaca
  (read-receipt), dan mengembalikan `read_up_to` = id pesan terakhir milikku sendiri yang
  sudah dibaca lawan bicara (dipakai untuk centang ✓✓)
- Auto-stop polling saat `status == "ended"`

### 6.3 File Upload di Chat

- Format: JPG, JPEG, PNG saja
- Ukuran maksimal: 2MB
- Nama file: `UUID.ext` (mencegah path traversal & collision)
- Lokasi: `app/static/chat_uploads/`
- Validasi ganda: ekstensi file + ukuran (seek ke end, cek, seek kembali)

### 6.4 Tampilan Chat — Konsep WhatsApp (2026-08-05)

UI ruang chat (`chat/room.html`) mengadopsi pola interaksi ala WhatsApp. Ditulis
awalnya di atas mekanisme polling; sejak §6.5 (2026-08-11) transport utamanya
sudah WebSocket, tapi konsep UI di bawah ini tidak berubah:

- **Header**: avatar bulat + label anonim ("Pendengar" untuk user, "Curhat #KODE"
  untuk psikolog) + baris status (`Online` / `Menunggu pendengar…` / `Mengetik…` /
  `Sesi berakhir`), diperbarui tiap poll.
- **Wallpaper**: pola titik halus di background area pesan (`.chat-wallpaper`), warna
  mengikuti brand, bukan aset WhatsApp asli.
- **Pemisah tanggal**: pill "Hari ini" / "Kemarin" / tanggal, otomatis muncul saat
  tanggal pesan berganti (helper `day_label()` di `app/utils.py`).
- **Centang kirim/baca**: `done` (abu-abu, sudah terkirim) -> `done_all` berwarna
  (sudah dibaca lawan bicara), berbasis field `Message.is_read` + `read_up_to` dari poll.
- **Indikator mengetik**: `POST /curhat/{code}/typing` men-set `user_typing_until` /
  `psikolog_typing_until` di `ChatSession` (window 4 detik), dibaca lawan bicara lewat
  `other_typing` di response poll. Ping di-throttle client-side (maks. 1x/2 detik saat mengetik).
- **Kirim gambar**: tombol attach + preview sebelum kirim — sebelumnya `MessageForm`
  sudah punya field `image` dan backend sudah menyimpannya, tapi **UI tidak pernah
  menampilkan input file maupun bubble gambar sama sekali** (gap tersembunyi, baru
  ketahuan & diperbaiki di sesi ini).

### 6.5 Transport Real-time — WebSocket (2026-08-11)

Chat sebelumnya polling HTTP tiap 2.5 detik untuk semua update (pesan baru,
status, mengetik, read receipt). Sekarang push lewat WebSocket
(Flask-SocketIO + gevent) — polling tetap ada tapi cuma jaring pengaman
lambat (15 detik) kalau koneksi socket putus.

**Arsitektur — hybrid, bukan full rewrite:**
- Aksi yang butuh CSRF/upload file/audit log/deteksi krisis (kirim pesan,
  akhiri sesi) **tetap lewat route REST biasa** di `app/routes/chat.py` —
  tidak dipindah ke socket, supaya semua proteksi yang sudah ada (CSRF,
  validasi ukuran gambar, `check_crisis()`, `log_audit()`) tidak perlu ditulis
  ulang untuk jalur socket.
- Setelah route REST commit ke DB, ia **juga** `socketio.emit(...)` ke room
  (nama room = `session_code`) supaya pihak lain dapat update instan tanpa
  nunggu poll berikutnya.
- Event dari client ke server (`join`, `typing`, `mark_read`) di-handle di
  `app/sockets.py` — dipakai untuk hal yang murni real-time/tidak butuh
  proteksi CSRF (typing indicator, tandai-sudah-baca).

**Event Socket.IO:**

| Event | Arah | Payload | Dipicu oleh |
|---|---|---|---|
| `join` | client→server | `{code}` | Saat koneksi socket dibuka / reconnect |
| `typing` | client→server | `{code}` | User mengetik (throttle 2 detik) |
| `mark_read` | client→server | `{code}` | Pesan baru dari lawan bicara masuk ke layar |
| `new_message` | server→room | pesan (sama shape dgn REST) | `POST /send` berhasil |
| `status_change` | server→room | `{status}` | Psikolog terima sesi / sesi diakhiri |
| `typing` | server→room (kecuali pengirim) | `{role}` | Relay dari client `typing` |
| `read_receipt` | server→room | `{read_up_to}` | Relay dari client `mark_read` |

**Dedup di client:** karena `new_message` di-broadcast ke SELURUH room
(termasuk pengirim sendiri — `socketio.emit` dari route REST bukan dari
socket handler, jadi tidak ada "current socket" buat `include_self=False`),
`room.html` melacak `renderedIds` (Set) supaya pesan yang sudah dirender dari
response AJAX `/send` tidak dirender dobel saat broadcast socket-nya nyampe.

**Gevent monkey-patch:** wajib jadi baris PALING AWAL di `run.py`/`wsgi.py`
(sebelum import lain, termasuk `db.py`/PyMySQL) — kalau tidak, cooperative
concurrency gevent tidak berlaku benar buat driver DB & socket standard
library. Lihat komentar di kedua file.

**⚠️ Catatan deployment production:** Waitress (server Windows yang
didokumentasikan di §1.1/AGENTS.md) **tidak support WebSocket sama sekali**.
Kalau dijalankan lewat waitress, chat tetap jalan (Socket.IO client otomatis
fallback ke long-polling — sudah dikonfigurasi `transports:["websocket","polling"]`
di `room.html`), tapi tidak dapat manfaat penuh WebSocket. Untuk WebSocket
sungguhan di production:
- **Linux**: `gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:8000 wsgi:app`
- **Windows**: jalankan lewat `python run.py` (pakai gevent's built-in
  production-capable WSGI server), bukan `waitress-serve`.

Divalidasi end-to-end lewat client `python-socketio` sungguhan (bukan cuma
HTTP) dengan `transports=["websocket"]` dipaksa (tidak fallback polling) —
login dua sisi, buka sesi (status_change diterima instan), kirim pesan
(new_message instan ke kedua sisi), typing indicator, mark_read (read_receipt
instan), akhiri sesi (status_change instan). Semua 8 tahap lolos.

---

## 7. Design System Visual

> **Sumber tunggal:** semua token di bawah didefinisikan SATU KALI di
> `app/templates/components/_design_tokens.html`, di-`include` oleh `base.html`
> (publik) dan `base_dashboard.html` (dashboard) — bukan didefinisikan ulang
> per file. Kalau mau ubah warna/font, edit partial itu saja, jangan
> duplikasi ke base template manapun.
>
> **Update 2026-08-05:** sebelumnya `base_dashboard.html` punya
> `tailwind.config` sendiri yang beda dari `base.html` (hijau `#064e3b` vs
> `#0A3622`, font Plus Jakarta Sans vs Be Vietnam Pro) — sudah disatukan.
> Efek samping yang ikut kebenerin: skala `brand-50`…`brand-500` dipakai
> ~99x di template dashboard tapi TIDAK PERNAH terdefinisi di config lama
> (cuma `brand-600` s/d `brand-900` yang ada) — Tailwind CDN diam-diam
> tidak menghasilkan CSS apa pun untuk kelas yang undefined, jadi elemen
> itu efektif tidak berwarna sama sekali sebelum perbaikan ini.

### 7.1 Color Palette

| Token | Hex | Penggunaan |
|-------|-----|------------|
| `primary` | `#0A3622` | Deep Forest Green — background utama, CTA, sidebar |
| `primary-light` | `#0D422A` | Variant gelap untuk card di atas primary |
| `brand-50…900` | `#EAF6EF` -> `#0A3622` | Skala penuh warna primary (dipakai halaman dashboard); `brand-900` = `primary` |
| `accent` / `accent-hover` / `accent-soft` | `#C8F31D` / `#B8E312` / `#E6FA8C` | Lime Green — highlight, badge, CTA sekunder |
| `surface` | `#F9F9F8` | Background halaman public |
| `on-surface` | `#1A1C1C` | Teks utama |
| `on-surface-variant` | `#444945` | Teks sekunder |
| `error` | `#BA1A1A` | Error state, crisis alert, laporan |
| `error-container` | `#FFDAD6` | Background error ringan |

### 7.2 Typography

Satu font heading untuk seluruh aplikasi (publik & dashboard): **Be Vietnam Pro**.

| Elemen | Font | Weight | Size |
|--------|------|--------|------|
| Heading (H1) | Be Vietnam Pro | 700-800 | 48-60px (`text-5xl`/`text-6xl`) |
| Heading (H2) | Be Vietnam Pro | 700 | 36-48px (`text-4xl`/`text-5xl`) |
| Heading (H3) | Be Vietnam Pro | 700 | 20-24px (`text-xl`/`text-2xl`) |
| Body text | Inter | 400 | 14-15px |
| Small/Caption | Inter | 500-600 | 12-13px |
| Button | Inter/Be Vietnam Pro | 700 | 14-15px |

### 7.3 Border Radius

| Token | Value | Penggunaan |
|-------|-------|------------|
| `rounded-custom` | `2rem` (32px) | Card utama, hero section |
| `rounded-2xl` | `1rem` (16px) | Card dashboard, chat bubble |
| `rounded-xl` | `0.75rem` (12px) | Input field, sidebar link |
| `rounded-full` | `9999px` | Button, badge, avatar, tab toggle |

### 7.4 Shadow

```css
.ambient-shadow { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05); }
```

Dipakai di semua card yang "mengambang" di atas surface.

### 7.5 Layout: Dua Sistem

**Public pages** (landing, forum, about, auth):
- Layout: full-width dengan `max-w-container-max-width` (1200px) + horizontal padding
- Navbar sticky di atas + footer di bawah
- Template: `base.html`

**Dashboard pages** (semua halaman yang butuh login):
- Layout: sidebar kiri 264px (Forest Green) + main content area kanan
- Top bar sticky dengan page title + notif bell + avatar
- Sidebar collapsible di mobile (hamburger toggle)
- Template: `base_dashboard.html`

### 7.6 Halaman Auth — Split Screen

```
┌────────────────────────┬──────────────────────────┐
│                        │                          │
│   HERO IMAGE           │     FORM AREA            │
│   (Unsplash grayscale  │                          │
│    + primary overlay)  │   [Daftar] [Masuk]       │
│                        │                          │
│   Badge: "Ruang Aman"  │   ┌──────────────────┐   │
│                        │   │  Form Register   │   │
│   Headline:            │   │  atau Login      │   │
│   "Mulailah Perjalanan │   │  (toggle tab)    │   │
│    Menuju Ketenangan"  │   └──────────────────┘   │
│                        │                          │
│   Value props:         │   --- Atau lanjutkan --- │
│   ✓ 100% Anonim        │   [Google Login]         │
│   ✓ Gratis Selamanya   │   [Masuk Tamu]           │
│                        │                          │
│   w-1/2                │   w-1/2                  │
└────────────────────────┴──────────────────────────┘
```

### 7.7 Landing Page — Sections

1. **Hero** — heading besar + CTA + collage image (blob shape + rotating badge SVG)
2. **Marquee strip** — text berjalan di background primary
3. **About section** — 2 kolom: grid gambar + progress bars
4. **Stats row** — 4 angka besar (sesi, pembimbing, komunitas, rating) dengan AOS animation
5. **Services** — 3 card layanan (chat, forum, mood) di background primary
6. **CTA final** — card besar rounded-3rem dengan blur decorative elements

Animasi: AOS library, `duration: 800ms`, `once: true`, `easing: ease-out-cubic`

---

## 8. Admin Panel — Full Control

### 8.1 Dashboard Admin

```
┌──────────────────────────────────────────────────────┐
│  ⚠️ CRISIS ALERT (jika ada sesi krisis aktif)        │
├──────────────────────────────────────────────────────┤
│  [Chat Hari Ini] [Sesi Aktif] [Menunggu] [Laporan] [User] │
├──────────────────────────────────────────────────────┤
│  [Kelola User] [Sesi Chat] [Forum Moderasi] [+ Pendengar]  │
├─────────────────────┬────────────────────────────────┤
│  Laporan Terbaru    │  Audit Log Terbaru             │
│  (pending reports)  │  (login, crisis, ban, dll)     │
└─────────────────────┴────────────────────────────────┘
```

### 8.2 Kemampuan Admin

| Area | Aksi yang Bisa Dilakukan |
|------|--------------------------|
| **Users** | Lihat semua, search, filter role, ban/unban, ubah role (user↔psikolog↔admin), verify/unverify psikolog |
| **Sessions** | Lihat semua sesi (filter status + crisis), baca isi chat lengkap, force-end sesi aktif |
| **Forum** | Lihat semua post (publik + hidden), sembunyikan/tampilkan post, sembunyikan/tampilkan komentar |
| **Reports** | Lihat laporan (filter status), abaikan atau sembunyikan konten yang dilaporkan |
| **Audit Log** | Lihat semua log (paginated), filter berdasarkan aksi, trace IP address |
| **Psikolog** | Buat akun pendengar baru (dengan must_change_password), verifikasi psikolog |

---

## 9. User Flow: Edit Profil & Hapus Akun

### 9.1 Edit Profil (User & Psikolog)

```
/u/settings atau /psikolog/settings
        │
        ├── Section 1: Edit Profil
        │   ├── Upload avatar (JPG/PNG max 2MB -> /static/avatars/UUID.ext)
        │   ├── Ubah username (unique check)
        │   ├── Ubah email (unique check)
        │   ├── Ubah nama lengkap
        │   └── Ubah bio
        │
        ├── Section 2: Ubah Password
        │   ├── Input password saat ini (verify)
        │   ├── Input password baru (8+ char, uppercase, number)
        │   └── Konfirmasi password baru
        │
        └── Section 3: Hapus Akun (hanya user)
            ├── Ketik "HAPUS" untuk konfirmasi
            └── Aksi:
                ├── is_active_account = False
                ├── email -> "deleted_{id}@removed.local"
                ├── username -> "deleted_{id}"
                ├── full_name, bio -> None
                ├── AuditLog "account_deleted"
                ├── Logout otomatis
                └── Data chat/forum tetap ada (anonim)
```

### 9.2 Kepatuhan UU PDP

- User bisa mengakses data pribadinya (halaman settings)
- User bisa memperbarui data (edit profil)
- User bisa menghapus akun (anonimisasi data)
- Privacy Policy menjelaskan data apa yang dikumpulkan, berapa lama disimpan, dan hak user
- Halaman Privacy Policy dan Terms of Service tersedia dan di-link dari footer

---

## 10. Sistem Notifikasi

### 10.1 Arsitektur

```
Event trigger ──► send_notification(user_id, title, message, link, type)
                        │
                        ▼
                  INSERT notifications table
                        │
                        ▼
              context_processor notif_count
                        │
                        ▼
               Bell icon badge di header
                        │
                  User klik bell
                        │
                        ▼
                  /notif/ — list notifikasi
                        │
                  Klik notif -> mark read + redirect ke link
```

### 10.2 Tipe Notifikasi

| Type | Icon | Warna | Trigger |
|------|------|-------|---------|
| `crisis` | warning | Merah | Keyword krisis terdeteksi di chat |
| `comment` | chat_bubble | Biru | Seseorang mengomentari cerita user |
| `session` | forum | Lime | Sesi chat berakhir |
| `info` | notifications | Abu-abu | Verifikasi psikolog, info umum |

---

## 11. Multi-Environment Configuration

```python
# config.py
class Config:           # Base — shared settings
class DevelopmentConfig # DEBUG=True
class ProductionConfig  # DEBUG=False, SECURE cookies, SECRET_KEY wajib dari env
class TestingConfig     # SQLite in-memory, CSRF off
```

Selection via `FLASK_ENV` environment variable atau parameter `create_app()`.

---

## 12. File Upload Architecture

```
Upload request
      │
      ▼
save_upload(file_storage, subfolder)
      │
      ├── Check: allowed extension? (jpg, jpeg, png)
      ├── Check: size ≤ 2MB? (seek to end, read position, seek back)
      ├── Generate: UUID hex + original extension
      ├── Ensure: target directory exists (makedirs)
      ├── Save: file to app/static/{subfolder}/{uuid}.{ext}
      └── Return: filename (or None on failure)
```

Subfolder yang dipakai:
- `avatars/` — foto profil user/psikolog
- `chat_uploads/` — gambar lampiran di chat

---

## 13. Logging & Monitoring

### 13.1 Application Log

- File: `logs/ceritakita.log`
- Format: `[timestamp] LEVEL in module: message`
- Rotation: max 1MB per file, 10 backup files
- Level: INFO (production), DEBUG (development)

### 13.2 Audit Trail

Database-level audit via model `AuditLog`. Setiap aksi penting memanggil `log_audit()` yang menyimpan user_id, action, target, detail, dan IP address.

---

## 14. Endpoint Reference

### Public (tanpa login)

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/` | Landing page (redirect ke dashboard jika login) |
| GET | `/tentang` | About page |
| GET | `/darurat` | Emergency help page |
| GET | `/privasi` | Privacy policy |
| GET | `/ketentuan` | Terms of service |
| GET | `/auth/login` | Halaman login (tab Masuk) |
| GET | `/auth/register` | Halaman register (tab Daftar) |
| POST | `/auth/login` | Proses login |
| POST | `/auth/register` | Proses register |
| GET | `/auth/logout` | Logout |
| GET | `/forum/` | Feed forum (read-only) |
| GET | `/forum/post/{id}` | Detail post (read-only) |

### User (role: user)

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/u/dashboard` | Dashboard user |
| GET/POST | `/u/settings` | Edit profil, ubah password, hapus akun |
| GET | `/curhat/` | Pilih cara curhat |
| POST | `/curhat/start` | Mulai sesi baru |
| GET | `/curhat/{code}` | Masuk ruang chat |
| GET | `/curhat/{code}/messages` | API polling pesan (JSON) |
| POST | `/curhat/{code}/send` | Kirim pesan (+ upload gambar) |
| POST | `/curhat/{code}/end` | Akhiri sesi |
| GET/POST | `/forum/new` | Tulis cerita baru |
| POST | `/forum/post/{id}/like` | Like post (JSON) |
| GET/POST | `/forum/post/{id}/report` | Laporkan post |
| GET/POST | `/mood/` | Mood tracker |

### Psikolog (role: psikolog)

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/psikolog/dashboard` | Dashboard + antrean |
| GET | `/psikolog/take/{code}` | Terima sesi waiting |
| GET | `/psikolog/profile` | Lihat profil sendiri |
| GET/POST | `/psikolog/settings` | Edit profil, ubah password |

### Admin (role: admin)

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/admin/dashboard` | Overview + crisis alert |
| GET | `/admin/users` | Daftar user (search, filter role) |
| POST | `/admin/users/{id}/toggle` | Ban/unban user |
| POST | `/admin/users/{id}/change-role` | Ubah role |
| POST | `/admin/users/{id}/verify` | Verify/unverify psikolog |
| GET/POST | `/admin/psikolog/new` | Buat akun psikolog |
| GET | `/admin/sessions` | Daftar sesi (filter status, crisis) |
| GET | `/admin/sessions/{code}/view` | Baca isi chat |
| POST | `/admin/sessions/{code}/end` | Force-end sesi |
| GET | `/admin/forum` | Moderasi forum |
| POST | `/admin/forum/post/{id}/toggle` | Hide/unhide post |
| POST | `/admin/forum/comment/{id}/toggle` | Hide/unhide komentar |
| GET | `/admin/reports` | Daftar laporan |
| POST | `/admin/reports/{id}/resolve` | Resolve/dismiss laporan |
| GET | `/admin/logs` | Audit log (paginated) |

### Notifikasi (semua role)

| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/notif/` | List notifikasi |
| GET | `/notif/read/{id}` | Tandai dibaca + redirect |
| POST | `/notif/read-all` | Tandai semua dibaca |
| GET | `/notif/count` | Count unread (JSON) |

---

## 15. Keputusan Desain & Trade-offs

| Keputusan | Alasan | Trade-off |
|-----------|--------|-----------|
| Polling 2.5s, bukan WebSocket | Simpel untuk Laragon dev environment, zero infra tambahan | Boros request (24 user = 576 req/menit), delay 0-2.5 detik |
| Tailwind CDN, bukan build | Tidak butuh Node.js/npm di setup | File CSS lebih besar, tidak bisa tree-shake |
| Password hash (scrypt) | Default Werkzeug, quantum-resistant | Slower than bcrypt, tapi acceptable |
| Denormalized `likes_count` | Satu query untuk display, tanpa JOIN | Bisa inconsistent kalau ada race condition |
| Session code `CK-XXXX` (4 digit) | Mudah diingat/dibaca | Hanya 10.000 kemungkinan — collision di scale besar |
| Anonimisasi saat hapus akun, bukan hard delete | Data forum/chat tetap utuh untuk komunitas | Storage tidak berkurang |
| Single-file templates (CSS+JS inline) | Tidak butuh build pipeline | Harder to maintain kalau scale besar |

---

## 16. Roadmap: Yang Belum Diimplementasi

> **Update 2026-08-05:** Forgot password sudah diimplementasikan (Flask-Mail,
> lihat `app/routes/auth.py`). Tanpa `MAIL_SERVER` di `.env`, email tidak benar-benar
> terkirim — link reset dicatat ke `logs/ceritakita.log` (`MAIL_SUPPRESS_SEND`,
> lihat `.env.example`) supaya tetap bisa ditest di dev lokal.
>
> Email verification saat register sempat diimplementasikan di tanggal yang sama,
> lalu **dihapus lagi** atas permintaan user — register sekarang langsung
> auto-login seperti semula, tidak ada gate verifikasi di `login()`.
>
> **Update 2026-08-11:** WebSocket real-time chat sudah diimplementasikan
> (Flask-SocketIO + gevent). Lihat §6.5 untuk detail arsitektur & catatan
> deployment production (waitress di Windows tidak support WebSocket).

| Prioritas | Fitur | Dependency |
|-----------|-------|------------|
| Medium | Database backup otomatis | Cron job + mysqldump |
| Medium | Sentry error tracking | Sentry account (free tier) |
| Medium | Upload dokumen verifikasi psikolog | File storage + review workflow |
| Low | Modul pelatihan listener | Content authoring system |
| Low | Google OAuth login | Google OAuth credentials |
| Low | End-to-end encryption chat | Client-side crypto library |
| Low | Mobile app (React Native) | Reuse Flask API backend |

---

*Dokumen ini merupakan living document dan diperbarui seiring perkembangan aplikasi.*
