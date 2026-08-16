/**
 * Service worker RuangCeritamu — sengaja MINIMAL.
 *
 * App ini dinamis (session/login-based) dan sekarang punya chat real-time
 * lewat WebSocket, jadi TIDAK cache halaman HTML atau respons API — cache
 * halaman yang butuh login bisa bocor ke device lain yang share browser,
 * atau nampilin CSRF token basi yang bakal gagal pas submit form.
 *
 * Cuma dua hal yang dilakukan:
 *  1. Cache aset statis genuinely static (ikon, manifest) supaya instalasi
 *     PWA cepat & hemat bandwidth di kunjungan berikutnya.
 *  2. Kalau navigasi (buka halaman) gagal karena offline, tampilkan
 *     offline.html alih-alih error browser polos.
 */
const CACHE_NAME = "ceritakita-static-v1";
const STATIC_ASSETS = [
  "/static/offline.html",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  // Navigasi (buka halaman) — network-first, fallback ke offline.html.
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() => caches.match("/static/offline.html"))
    );
    return;
  }

  // Aset statis genuinely static — cache-first.
  if (STATIC_ASSETS.some((a) => req.url.endsWith(a))) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req))
    );
  }
  // Selain itu (API, chat_uploads, dsb) — biarkan lewat network seperti biasa.
});
