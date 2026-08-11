# PRD — Product Requirements Document

## CeritaKita: Platform Curhat Anonim untuk Anak Muda Indonesia

| Field | Detail |
|-------|--------|
| **Nama Produk** | CeritaKita |
| **Versi Dokumen** | 2.0 |
| **Status** | In Development |
| **Tanggal** | 2025 |
| **Author** | Tim Pengembang CeritaKita |
| **Stakeholder** | Product Owner, Backend Engineer, Frontend Engineer, UI/UX Designer |

---

## 1. Executive Summary

### 1.1 Latar Belakang

Kesehatan mental anak muda Indonesia berada di titik kritis. Data Kemenkes RI menunjukkan bahwa 1 dari 3 remaja Indonesia mengalami masalah kesehatan mental, namun hanya 8% yang mendapatkan penanganan profesional. Hambatan utama meliputi biaya konsultasi yang mahal (Rp 200.000–500.000 per sesi), stigma sosial yang masih kuat di masyarakat, keterbatasan jumlah psikolog klinis (hanya sekitar 2.500 untuk 270 juta penduduk), serta keengganan mengungkapkan identitas saat bercerita tentang masalah pribadi.

### 1.2 Solusi yang Ditawarkan

CeritaKita adalah platform peer-support (dukungan sebaya) berbasis web yang menyediakan ruang curhat anonim gratis untuk anak muda Indonesia. Platform ini menghubungkan user yang membutuhkan tempat bercerita dengan relawan pendengar terlatih melalui tiga kanal utama: chat 1:1 anonim dengan matchmaking acak, forum cerita publik dengan nama samaran, dan mood tracker harian untuk self-awareness.

### 1.3 Penegasan Batasan

CeritaKita **bukan layanan terapi profesional**. Pendengar adalah relawan terlatih dasar yang dilatih untuk mendengarkan dengan empati, bukan untuk mendiagnosis atau memberikan treatment. Untuk situasi krisis, platform menyediakan mekanisme eskalasi otomatis ke hotline profesional (119 ext. 8).

### 1.4 Metrik Keberhasilan

| Metrik | Target 6 Bulan | Target 12 Bulan |
|--------|----------------|-----------------|
| User terdaftar | 500 | 2.000 |
| Sesi chat selesai per bulan | 100 | 500 |
| Rata-rata waktu tunggu sesi | < 10 menit | < 5 menit |
| Forum post per bulan | 50 | 200 |
| Mood log per bulan | 200 | 1.000 |
| Relawan pendengar aktif | 15 | 50 |
| Tingkat kepuasan user (survey) | > 80% | > 85% |
| Crisis detection accuracy | > 70% | > 85% |
| Uptime | 99% | 99.5% |

---

## 2. User Persona

### 2.1 Persona: Rina — User (Pencari Dukungan)

| Atribut | Detail |
|---------|--------|
| **Usia** | 19 tahun |
| **Pekerjaan** | Mahasiswi semester 4, Fakultas Psikologi |
| **Lokasi** | Surabaya |
| **Perangkat** | Smartphone Android (utama), laptop (sesekali) |
| **Konteks** | Mengalami tekanan akademik dan konflik keluarga. Tidak punya teman dekat yang cukup dipercaya untuk curhat. Tidak mampu biaya psikolog. Takut dihakimi kalau cerita ke orang yang dikenal. |
| **Kebutuhan** | Tempat bercerita yang aman tanpa identitas terlihat. Pendengar yang tidak menghakimi. Tidak ingin proses ribet (daftar lama, verifikasi KTP, dll). |
| **Frustrasi** | Pernah coba aplikasi kesehatan mental tapi berbayar. Chat bot tidak terasa manusiawi. Takut data pribadinya bocor. |
| **Quote** | "Aku cuma butuh seseorang yang mau dengar tanpa bilang 'kamu kurang bersyukur'." |

### 2.2 Persona: Kak Andi — Psikolog/Pendengar (Relawan)

| Atribut | Detail |
|---------|--------|
| **Usia** | 24 tahun |
| **Pekerjaan** | Fresh graduate S1 Psikologi, sedang gap year |
| **Motivasi** | Ingin mengaplikasikan ilmu psikologi, membangun portfolio volunteering, merasa terpanggil membantu sesama. |
| **Kebutuhan** | Dashboard yang jelas untuk melihat antrean. Panduan singkat cara menangani sesi. Tahu kapan harus eskalasi ke profesional. Merasa aman — tidak ingin identitasnya diketahui user. |
| **Frustrasi** | Pernah jadi relawan di platform lain tapi tidak ada training. Tidak tahu batasan perannya. |
| **Quote** | "Aku bukan psikolog berlisensi, tapi aku bisa hadir dan mendengar." |

### 2.3 Persona: Admin Dian — Administrator Platform

| Atribut | Detail |
|---------|--------|
| **Usia** | 28 tahun |
| **Pekerjaan** | Founder/coordinator CeritaKita |
| **Kebutuhan** | Visibility penuh atas platform: siapa online, sesi mana yang bermasalah, konten mana yang dilaporkan. Kemampuan intervensi cepat (ban user, tutup sesi, hide konten). Data untuk laporan ke donor/partner. |
| **Frustrasi** | Kalau ada krisis tapi tidak tahu sampai terlambat. Relawan yang tidak mengikuti kode etik. Konten trolling yang merusak safe space. |
| **Quote** | "Satu insiden krisis yang tidak tertangani bisa menghancurkan kepercayaan seluruh komunitas." |

---

## 3. Arsitektur Role & Permission

### 3.1 Role Hierarchy

```
GUEST (tanpa login)
  └── Bisa: lihat landing, forum (read-only), about, darurat, privasi, ketentuan
  └── Tidak bisa: chat, posting, komentar, mood tracker

USER (pendaftaran sendiri)
  └── Semua akses Guest
  └── Bisa: mulai sesi chat, posting forum, komentar, mood tracker, edit profil, hapus akun
  └── Tidak bisa: terima sesi, akses admin panel

PSIKOLOG (dibuat oleh admin)
  └── Bisa: lihat antrean, terima sesi, chat sebagai pendengar, edit profil
  └── Harus: ganti password setelah login pertama
  └── Harus: diverifikasi admin sebelum dianggap "terverifikasi"
  └── Tidak bisa: mulai sesi sebagai user, akses admin panel

ADMIN (dibuat manual atau via seed)
  └── Semua akses
  └── Bisa: kelola user (ban/unban/ganti role/verify), kelola sesi (lihat chat/tutup paksa), moderasi forum (hide/unhide), kelola laporan, lihat audit log, buat akun psikolog
```

### 3.2 Matriks Permission Detail

| Aksi | Guest | User | Psikolog | Admin |
|------|-------|------|----------|-------|
| Lihat landing page | ✅ | ✅ | ✅ | ✅ |
| Lihat forum (read-only) | ✅ | ✅ | ✅ | ✅ |
| Lihat halaman darurat | ✅ | ✅ | ✅ | ✅ |
| Lihat privacy policy & TOS | ✅ | ✅ | ✅ | ✅ |
| Daftar akun | ✅ | — | — | — |
| Login | ✅ | ✅ | ✅ | ✅ |
| Mulai sesi curhat | ❌ | ✅ | ❌ | ❌ |
| Posting forum | ❌ | ✅ | ✅ | ✅ |
| Komentar forum | ❌ | ✅ | ✅ | ✅ |
| Like post | ❌ | ✅ | ✅ | ✅ |
| Laporkan post | ❌ | ✅ | ✅ | ✅ |
| Catat mood | ❌ | ✅ | ❌ | ❌ |
| Edit profil sendiri | ❌ | ✅ | ✅ | ❌ |
| Ubah password | ❌ | ✅ | ✅ | ❌ |
| Hapus akun sendiri | ❌ | ✅ | ❌ | ❌ |
| Lihat antrean sesi | ❌ | ❌ | ✅ | ✅ |
| Terima sesi | ❌ | ❌ | ✅ | ❌ |
| Chat sebagai pendengar | ❌ | ❌ | ✅ | ❌ |
| Lihat semua user | ❌ | ❌ | ❌ | ✅ |
| Ban/unban user | ❌ | ❌ | ❌ | ✅ |
| Ubah role user | ❌ | ❌ | ❌ | ✅ |
| Verify psikolog | ❌ | ❌ | ❌ | ✅ |
| Buat akun psikolog | ❌ | ❌ | ❌ | ✅ |
| Lihat isi chat orang lain | ❌ | ❌ | ❌ | ✅ |
| Tutup paksa sesi | ❌ | ❌ | ❌ | ✅ |
| Hide/unhide post & komentar | ❌ | ❌ | ❌ | ✅ |
| Resolve laporan | ❌ | ❌ | ❌ | ✅ |
| Lihat audit log | ❌ | ❌ | ❌ | ✅ |
| Lihat notifikasi | ❌ | ✅ | ✅ | ✅ |

---

## 4. Functional Requirements

### FR-01: Registrasi & Autentikasi

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01.1 | User bisa mendaftar dengan username (samaran), email, dan password | P0 |
| FR-01.2 | Password wajib minimal 8 karakter, mengandung 1 huruf besar dan 1 angka | P0 |
| FR-01.3 | Username dan email harus unik di seluruh sistem | P0 |
| FR-01.4 | User bisa login menggunakan email ATAU username | P0 |
| FR-01.5 | Login gagal lebih dari 10x per menit di-rate limit (HTTP 429) | P0 |
| FR-01.6 | Registrasi di-rate limit 5x per menit | P0 |
| FR-01.7 | Session cookie bersifat httpOnly dan SameSite=Lax | P0 |
| FR-01.8 | Halaman auth menampilkan form login dan register dalam satu halaman dengan tab toggle | P1 |
| FR-01.9 | Setiap login/logout dicatat di audit log (termasuk IP address) | P1 |
| FR-01.10 | Psikolog yang dibuat admin wajib ganti password saat login pertama (flag must_change_password) | P1 |

### FR-02: Chat Anonim 1:1

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-02.1 | User memilih topik (opsional) dan klik "Mulai Curhat" untuk membuat sesi baru | P0 |
| FR-02.2 | Sistem generate kode sesi unik format CK-XXXX (4 digit random) | P0 |
| FR-02.3 | Sesi baru berstatus "waiting" sampai psikolog menerima | P0 |
| FR-02.4 | User hanya boleh punya 1 sesi aktif/waiting pada satu waktu | P0 |
| FR-02.5 | Psikolog melihat daftar sesi waiting di dashboard dan bisa klik "Terima" | P0 |
| FR-02.6 | Saat psikolog terima, status berubah ke "active" dan psikolog_id di-assign | P0 |
| FR-02.7 | Pesan dikirim via HTTP POST dan diambil via polling GET setiap 2.5 detik | P0 |
| FR-02.8 | Polling menggunakan cursor after_id supaya hanya ambil pesan baru | P0 |
| FR-02.9 | Kedua pihak bisa mengakhiri sesi kapan saja | P0 |
| FR-02.10 | Saat sesi diakhiri, notifikasi dikirim ke pihak lain | P1 |
| FR-02.11 | User dan psikolog tidak saling melihat data pribadi (username, email, dll) | P0 |
| FR-02.12 | User bisa mengirim gambar (JPG/PNG, max 2MB) di chat | P1 |
| FR-02.13 | Gambar disimpan dengan nama UUID random untuk keamanan | P1 |
| FR-02.14 | Admin bisa melihat isi chat siapa pun dan menutup paksa sesi | P0 |
| FR-02.15 | Banner "Sedang mencari pendengar..." ditampilkan saat status waiting | P1 |
| FR-02.16 | Banner darurat (hotline 119) selalu ditampilkan di bagian atas ruang chat | P0 |

### FR-03: Deteksi Keyword Krisis

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-03.1 | Setiap pesan chat dicek terhadap 30+ keyword krisis Bahasa Indonesia | P0 |
| FR-03.2 | Keyword meliputi: bunuh diri, mau mati, ingin mati, self-harm, gantung diri, overdosis, tidak ada harapan, dan variasinya | P0 |
| FR-03.3 | Pencocokan bersifat case-insensitive substring match | P0 |
| FR-03.4 | Jika terdeteksi: sesi ditandai has_crisis_flag=True | P0 |
| FR-03.5 | Jika terdeteksi: pesan individual ditandai is_crisis=True | P0 |
| FR-03.6 | Jika terdeteksi: entry dibuat di audit log (action: crisis_detected) | P0 |
| FR-03.7 | Jika terdeteksi: notifikasi dikirim ke SEMUA admin (tipe: crisis) | P0 |
| FR-03.8 | Jika terdeteksi: logger WARNING ditulis ke application log | P1 |
| FR-03.9 | Di frontend: pesan krisis ditandai visual (ring merah) | P1 |
| FR-03.10 | Di frontend: banner darurat muncul untuk user (hotline 119 clickable) | P0 |
| FR-03.11 | Di dashboard psikolog: sesi krisis ditandai icon ⚠️ | P1 |
| FR-03.12 | Di admin dashboard: alert merah muncul jika ada sesi krisis aktif | P0 |

### FR-04: Forum Cerita Publik

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-04.1 | User bisa membuat post dengan judul (min 5 char), konten (min 20 char), mood tag, dan nama samaran opsional | P0 |
| FR-04.2 | Mood tag pilihan: Lelah, Cemas, Sedih, Marah, Bingung, Syukur, Self-Care, Refleksi | P0 |
| FR-04.3 | Feed menampilkan post yang tidak di-hide, sortable: Terbaru atau Populer | P0 |
| FR-04.4 | Feed bisa difilter berdasarkan mood tag | P1 |
| FR-04.5 | Feed memiliki search box yang mencari di judul dan konten (ILIKE query) | P1 |
| FR-04.6 | Pagination: 10 post per halaman | P1 |
| FR-04.7 | Guest bisa membaca forum tanpa login | P0 |
| FR-04.8 | User yang login bisa like post (counter denormalisasi) | P1 |
| FR-04.9 | User yang login bisa komentar dengan nama samaran opsional | P0 |
| FR-04.10 | Saat ada komentar baru, notifikasi dikirim ke author post (kecuali self-comment) | P1 |
| FR-04.11 | User bisa melaporkan post dengan alasan (membuat entry Report) | P0 |
| FR-04.12 | Admin bisa hide/unhide post dan komentar | P0 |
| FR-04.13 | Post yang di-hide tidak muncul di feed (kecuali untuk admin) | P0 |

### FR-05: Mood Tracker

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05.1 | User bisa mencatat mood harian dengan pilihan: Senang, Biasa Saja, Sedih, Cemas, Overthinking | P0 |
| FR-05.2 | Setiap mood disertai emoji visual: 😊 😐 😭 😰 🌀 | P0 |
| FR-05.3 | User bisa menambahkan catatan singkat (opsional, max 1000 char) | P1 |
| FR-05.4 | Sistem menghitung mood dominan dalam 7 hari terakhir | P1 |
| FR-05.5 | Riwayat mood ditampilkan dalam list (30 entry terakhir) | P1 |
| FR-05.6 | Input mood menggunakan radio button visual (grid 5 kolom dengan emoji besar) | P1 |

### FR-06: Profil & Pengaturan Akun

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-06.1 | User dan psikolog bisa mengedit: username, email, nama lengkap, bio | P0 |
| FR-06.2 | User dan psikolog bisa upload foto profil (JPG/PNG, max 2MB) | P1 |
| FR-06.3 | Foto profil disimpan dengan nama UUID di /static/avatars/ | P1 |
| FR-06.4 | Username dan email baru harus unik (validasi di form level) | P0 |
| FR-06.5 | User dan psikolog bisa mengubah password (wajib input password lama) | P0 |
| FR-06.6 | Password baru harus memenuhi policy yang sama (8+ char, uppercase, number) | P0 |
| FR-06.7 | User bisa menghapus akun sendiri (ketik "HAPUS" untuk konfirmasi) | P0 |
| FR-06.8 | Penghapusan akun bersifat soft-delete: is_active_account=False, data pribadi dianonimkan (username -> deleted_ID, email -> deleted_ID@removed.local, full_name & bio -> null) | P0 |
| FR-06.9 | Setelah hapus akun, user di-logout otomatis | P0 |
| FR-06.10 | Setiap perubahan profil dan password dicatat di audit log | P1 |

### FR-07: Sistem Notifikasi

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-07.1 | Bell icon di header dashboard menampilkan badge count notifikasi unread | P0 |
| FR-07.2 | Halaman /notif/ menampilkan list semua notifikasi (terbaru di atas) | P0 |
| FR-07.3 | Notifikasi unread punya visual berbeda dari yang sudah dibaca (background accent) | P1 |
| FR-07.4 | Klik notifikasi -> tandai dibaca + redirect ke link tujuan | P0 |
| FR-07.5 | Tombol "Tandai semua dibaca" tersedia di halaman notifikasi | P1 |
| FR-07.6 | API endpoint /notif/count mengembalikan JSON count untuk polling frontend (opsional) | P2 |
| FR-07.7 | 4 tipe notifikasi: crisis (merah), comment (biru), session (lime), info (abu-abu) | P1 |
| FR-07.8 | Trigger otomatis: komentar baru -> author post, sesi berakhir -> pihak lain, krisis -> semua admin, verify psikolog -> psikolog | P0 |

### FR-08: Admin Panel (Full Control)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-08.1 | Admin dashboard menampilkan: stat overview (chat hari ini, sesi aktif, menunggu, laporan pending, total user), action shortcuts, laporan terbaru, audit log terbaru | P0 |
| FR-08.2 | Alert merah prominent jika ada sesi krisis aktif, dengan link langsung ke filter krisis | P0 |
| FR-08.3 | Admin bisa melihat daftar semua user dengan filter (role, search nama/email) | P0 |
| FR-08.4 | Admin bisa ban/unban user (toggle is_active_account) | P0 |
| FR-08.5 | Admin bisa mengubah role user (user ↔ psikolog ↔ admin) | P0 |
| FR-08.6 | Admin bisa verify/unverify psikolog (toggle is_verified) | P0 |
| FR-08.7 | Admin bisa membuat akun psikolog baru (dengan flag must_change_password) | P0 |
| FR-08.8 | Admin bisa melihat daftar semua sesi chat (filter: status, crisis only) | P0 |
| FR-08.9 | Admin bisa membaca isi chat siapa pun (view session) | P0 |
| FR-08.10 | Admin bisa menutup paksa sesi aktif (force-end) | P0 |
| FR-08.11 | Admin bisa melihat semua post forum (termasuk yang di-hide) | P0 |
| FR-08.12 | Admin bisa hide/unhide post dan komentar individual | P0 |
| FR-08.13 | Admin bisa melihat dan resolve laporan (dismiss atau hide konten) | P0 |
| FR-08.14 | Admin bisa melihat audit log lengkap (paginated, filterable per aksi) | P0 |
| FR-08.15 | Semua aksi admin dicatat di audit log dengan IP address | P0 |

### FR-09: Halaman Legal & Keselamatan

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-09.1 | Halaman Privacy Policy tersedia di /privasi, menjelaskan: data yang dikumpulkan, cara penggunaan, hak user (UU PDP), retensi data, kontak DPO | P0 |
| FR-09.2 | Halaman Terms of Service tersedia di /ketentuan, menjelaskan: batasan layanan, kode etik, usia minimum (13 tahun), disclaimer | P0 |
| FR-09.3 | Link Privacy Policy dan TOS ada di footer semua halaman | P0 |
| FR-09.4 | Halaman Bantuan Darurat (/darurat) menampilkan: hotline Kemenkes 119 ext. 8, Into The Light Indonesia, IGD terdekat | P0 |
| FR-09.5 | Link darurat ada di footer, sidebar dashboard, dan chat room | P0 |
| FR-09.6 | Halaman About (/tentang) menjelaskan misi platform dan penegasan batasan (bukan terapi profesional) | P1 |

---

## 5. Non-Functional Requirements

### NFR-01: Performa

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01.1 | Waktu loading halaman (TTFB) | < 500ms |
| NFR-01.2 | Waktu respons API polling chat | < 200ms |
| NFR-01.3 | Waktu pengiriman pesan chat | < 300ms |
| NFR-01.4 | Concurrent users supported | 50 (dev), 500 (prod dengan Gunicorn 4 workers) |
| NFR-01.5 | Database query time | < 100ms per query |

### NFR-02: Keamanan

| ID | Requirement |
|----|-------------|
| NFR-02.1 | Password di-hash dengan algoritma scrypt (Werkzeug default) |
| NFR-02.2 | CSRF protection aktif di semua form dan endpoint POST |
| NFR-02.3 | Rate limiting di endpoint sensitif (login, register) |
| NFR-02.4 | File upload divalidasi: ekstensi (whitelist), ukuran (max 2MB), nama (UUID random) |
| NFR-02.5 | SQL injection dicegah via ORM (SQLAlchemy parameterized queries) |
| NFR-02.6 | XSS dicegah via Jinja2 auto-escaping dan escapeHtml() di JavaScript |
| NFR-02.7 | Session cookie: httpOnly=True, SameSite=Lax, Secure=True (production) |
| NFR-02.8 | DEBUG=False di production config |
| NFR-02.9 | Audit trail untuk semua aksi sensitif |

### NFR-03: Ketersediaan & Reliability

| ID | Requirement |
|----|-------------|
| NFR-03.1 | Uptime target: 99% (development), 99.5% (production) |
| NFR-03.2 | Application logging dengan rotation (max 1MB, 10 backup files) |
| NFR-03.3 | Graceful error handling (custom 404, 500, 403, 429 pages) |
| NFR-03.4 | Database auto-create saat pertama kali dijalankan |
| NFR-03.5 | Flask-Migrate tersedia untuk schema migration tanpa data loss |

### NFR-04: Usability

| ID | Requirement |
|----|-------------|
| NFR-04.1 | Responsive design: desktop (1440px) dan mobile (390px) |
| NFR-04.2 | Semua UI dalam Bahasa Indonesia |
| NFR-04.3 | Sidebar dashboard collapsible di mobile (hamburger toggle) |
| NFR-04.4 | Flash messages untuk feedback aksi (success, error, info) dengan auto-dismiss 4-5 detik |
| NFR-04.5 | Empty states yang informatif di setiap list/table kosong |
| NFR-04.6 | Confirmation dialog sebelum aksi destruktif (hapus akun, tutup sesi, ban user) |

### NFR-05: Privasi & Kepatuhan Hukum

| ID | Requirement |
|----|-------------|
| NFR-05.1 | Kepatuhan UU PDP (UU No. 27 Tahun 2022): hak akses, koreksi, dan penghapusan data |
| NFR-05.2 | User bisa menghapus akun (soft-delete + anonimisasi) |
| NFR-05.3 | Privacy Policy dan Terms of Service tersedia dan dapat diakses publik |
| NFR-05.4 | Chat bersifat anonim — identitas user dan psikolog tidak saling terlihat |
| NFR-05.5 | Cookie hanya dipakai untuk session management, bukan tracking |

---

## 6. User Flow Detail

### 6.1 Flow: Registrasi User Baru

```
[Landing Page]
    │
    ▼ Klik "Daftar" atau CTA
[Halaman Auth — Tab "Daftar Baru"]
    │
    ├── Isi username (samaran)
    ├── Isi email
    ├── Isi password (8+ char, 1 uppercase, 1 number)
    │
    ▼ Klik "Daftar Sekarang"
[Server validasi]
    │
    ├── Gagal: error ditampilkan di bawah field yang bermasalah
    │
    ▼ Berhasil
[Auto-login + redirect ke /u/dashboard]
[Flash: "Akun berhasil dibuat!"]
[AuditLog: user_registered]
```

### 6.2 Flow: User Mulai Sesi Curhat

```
[User Dashboard]
    │
    ▼ Klik "Mulai Curhat" (sidebar atau card)
[Halaman Pilih — /curhat/]
    │
    ├── Opsi A: Chat Anonim 1:1
    │   ├── Pilih topik dropdown (opsional)
    │   ▼ Klik "Cari Pendengar"
    │   [Server: cek tidak ada sesi aktif]
    │   [Server: generate CK-XXXX unik]
    │   [Server: buat ChatSession(status=waiting)]
    │   ▼ Redirect ke /curhat/CK-XXXX
    │   [Ruang Chat — Banner "Mencari pendengar..."]
    │   [Polling setiap 2.5 detik]
    │       │
    │       ▼ Psikolog terima sesi
    │   [Banner hilang, status "Aktif"]
    │   [User mulai kirim pesan]
    │       │
    │       ▼ Salah satu pihak klik "Akhiri"
    │   [status=ended, notif ke pihak lain]
    │   [Redirect ke dashboard]
    │
    ├── Opsi B: Forum Cerita Publik
    │   ▼ Klik "Tulis Cerita"
    │   [Halaman new post — /forum/new]
    │   ▼ Submit cerita
    │   [Redirect ke detail post]
```

### 6.3 Flow: Psikolog Terima dan Handle Sesi

```
[Psikolog Login]
    │
    ▼ Redirect ke /psikolog/dashboard
[Dashboard: lihat antrean "waiting"]
    │
    ├── Sesi dengan flag krisis ⚠️ ditandai visual
    │
    ▼ Klik "Terima" pada sesi CK-XXXX
[Server: assign psikolog_id, status=active]
    ▼ Redirect ke /curhat/CK-XXXX
[Ruang Chat]
    │
    ├── Jika sesi punya crisis flag:
    │   └── Alert merah: "CRISIS TERDETEKSI — sarankan 119 ext. 8"
    │
    ├── Chat dengan user
    │   ├── Kirim teks
    │   └── Terima teks/gambar
    │
    ▼ Klik "Akhiri" atau user akhiri
[Redirect ke dashboard psikolog]
```

### 6.4 Flow: Admin Handle Crisis

```
[Admin Dashboard]
    │
    ▼ Alert merah: "⚠️ 2 Sesi Krisis Aktif"
[Klik "Lihat"]
    ▼
[Admin — Kelola Sesi, filter: Krisis]
    │
    ▼ Klik "Lihat" pada sesi CK-XXXX
[Admin — View Session]
    │
    ├── Baca seluruh isi chat
    ├── Pesan krisis ditandai ring merah
    │
    ├── Opsi A: Tutup paksa sesi
    │   ▼ Klik "Tutup Paksa"
    │   [AuditLog: session_force_ended]
    │
    ├── Opsi B: Kontak psikolog via channel lain
    │
    └── Opsi C: Monitor saja, biarkan psikolog handle
```

### 6.5 Flow: User Hapus Akun

```
[User — /u/settings]
    │
    ▼ Scroll ke bagian "Hapus Akun"
[Klik "Saya mengerti, tampilkan form..."]
    │
    ▼ Form muncul
[Ketik "HAPUS" di input field]
    ▼ Klik "Hapus Akun Saya"
[Server:]
    ├── is_active_account = False
    ├── username -> "deleted_{id}"
    ├── email -> "deleted_{id}@removed.local"
    ├── full_name, bio -> null
    ├── AuditLog: account_deleted
    ├── Logout user
    ▼
[Redirect ke landing page]
[Flash: "Akunmu sudah dihapus. Data pribadi telah dianonimkan."]
```

---

## 7. Data Model Summary

### 7.1 Entity Count & Relationships

| Entity | Kolom | Relasi |
|--------|-------|--------|
| **User** | 13 kolom | -> ChatSession (as user & as psikolog), ForumPost, ForumComment, MoodLog, Notification |
| **ChatSession** | 10 kolom | -> User (user_id, psikolog_id), Message |
| **Message** | 8 kolom | -> ChatSession, User (sender) |
| **ForumPost** | 9 kolom | -> User (author), ForumComment |
| **ForumComment** | 7 kolom | -> ForumPost, User |
| **MoodLog** | 5 kolom | -> User |
| **Report** | 8 kolom | -> User (reporter, resolved_by) |
| **AuditLog** | 8 kolom | -> User |
| **Notification** | 8 kolom | -> User |
| **Total** | **9 tabel, 76 kolom** | |

### 7.2 Enums

```
Role: admin | psikolog | user
SessionStatus: waiting | active | ended
Mood: happy | neutral | sad | anxious | overthink
MoodTag: Lelah | Cemas | Sedih | Marah | Bingung | Syukur | Self-Care | Refleksi
Topic: kuliah | karir | keluarga | percintaan | pertemanan | kesehatan_mental | lainnya
ReportStatus: pending | resolved | dismissed
NotifType: info | crisis | comment | session
```

---

## 8. API & Endpoint Summary

| Total Endpoints | 43 |
|-----------------|-----|
| Public (tanpa login) | 12 |
| User only | 12 |
| Psikolog only | 4 |
| Admin only | 15 |
| All authenticated | 4 (notifikasi) |

Endpoint detail lengkap tersedia di DESIGN.md Section 14.

---

## 9. Risiko & Mitigasi

| Risiko | Dampak | Probabilitas | Mitigasi |
|--------|--------|--------------|----------|
| User dalam krisis tidak terdeteksi | Kritis | Sedang | Keyword detection + banner darurat + notif admin + disclaimer di setiap halaman |
| Pendengar memberikan saran berbahaya | Tinggi | Rendah | Verifikasi admin, kode etik, admin bisa baca chat, flag must_change_password |
| Data user bocor | Tinggi | Rendah | Hash password, CSRF, httpOnly cookies, anonimisasi saat hapus akun |
| Trolling/spam di forum | Sedang | Tinggi | Report system, admin moderasi, hide/unhide, ban user |
| Server down saat user butuh bantuan | Tinggi | Rendah | Halaman darurat dengan hotline statis, disclaimer "bukan terapi profesional" |
| Polling chat membebani server | Sedang | Sedang | Cursor-based after_id, bisa migrasi ke WebSocket di masa depan |
| False positive crisis detection | Rendah | Sedang | Keyword match hanya trigger notifikasi, bukan blokir pesan, admin review final |
| Psikolog burn-out | Sedang | Sedang | Statistik sesi per psikolog terlihat di dashboard, admin bisa monitor beban |

---

## 10. Future Roadmap

### Phase 2 — Infrastruktur (membutuhkan service eksternal)

| Fitur | Dependency | Estimasi |
|-------|------------|----------|
| Forgot password (email reset dengan token expire) | Flask-Mail + Gmail SMTP | 1 minggu |
| Email verification saat registrasi | Flask-Mail + Gmail SMTP | 1 minggu |
| WebSocket real-time chat (ganti polling) | Flask-SocketIO + eventlet | 2 minggu |
| Database backup otomatis | Cron job + mysqldump + cloud storage | 3 hari |
| Error monitoring | Sentry (free tier) | 1 hari |

### Phase 3 — Fitur Lanjutan

| Fitur | Estimasi |
|-------|----------|
| Google OAuth login | 1 minggu |
| Upload dokumen verifikasi psikolog + review workflow admin | 2 minggu |
| Modul pelatihan listener (quiz-based) sebelum bisa terima sesi | 3 minggu |
| Push notification (browser) | 1 minggu |
| Dashboard analitik admin (chart trend, mood aggregate komunitas) | 2 minggu |
| Mobile app (React Native, reuse Flask API) | 2 bulan |
| End-to-end encryption chat | 1 bulan |
| AI-based crisis detection (NLP sentiment analysis, ganti keyword match) | 1 bulan |
| Multi-language support (Bahasa Daerah) | 2 minggu |
| Gamifikasi: Thank Card untuk listener, badge milestone | 2 minggu |

---

## 11. Acceptance Criteria Summary

Aplikasi dianggap **siap deploy (MVP)** jika memenuhi seluruh requirement **P0**, yaitu:

1. User bisa register, login, logout dengan password policy ketat
2. User bisa mulai sesi chat anonim 1:1 dan berkomunikasi dengan psikolog
3. Keyword krisis terdeteksi dan admin mendapat notifikasi
4. Forum berfungsi (buat post, komentar, laporkan)
5. Mood tracker berfungsi
6. Admin bisa mengelola seluruh platform (user, sesi, forum, laporan)
7. Privacy Policy dan Terms of Service tersedia
8. Halaman darurat dengan hotline resmi tersedia
9. Audit trail mencatat semua aksi penting
10. Rate limiting aktif di endpoint sensitif

---

*Dokumen ini merupakan living document dan akan diperbarui seiring perkembangan produk.*