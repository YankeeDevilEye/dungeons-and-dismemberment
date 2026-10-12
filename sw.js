// Offline cache for Dungeons & Dismemberment (relative paths; works under /<repo>/ on GitHub Pages)
const CACHE = 'dd-r26-f90c19555f';
const CORE = ["./","./assets/index-ChfivWSw.css","./assets/index-gN4LvFaD.js","./icon-180.png","./icon-192.png","./icon-512.png","./icon-maskable-512.png","./icon.svg","./index.html","./manifest.webmanifest"];
self.addEventListener('install', (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith('dd-') && k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', (e) => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (r.mode === 'navigate') { // network-first so new deploys show up; cached shell when offline
    e.respondWith(fetch(r.url, { cache: 'no-cache', credentials: 'same-origin' }).then((res) => { const cp = res.clone(); caches.open(CACHE).then((c) => c.put('./', cp)); return res; }).catch(() => caches.match('./')));
    return;
  }
  if (u.origin === location.origin || u.host.endsWith('fonts.googleapis.com') || u.host.endsWith('fonts.gstatic.com')) {
    e.respondWith(caches.match(r).then((hit) => hit || fetch(r).then((res) => { if (res.ok || res.type === 'opaque') { const cp = res.clone(); caches.open(CACHE).then((c) => c.put(r, cp)); } return res; })));
  }
});
