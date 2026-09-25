// Only the fixed public client shell is cached. API data needs an explicit save.
const CACHE = 'lazypromotion-preview-shell-v1';
const SHELL = ['/', '/app.mjs', '/model.mjs', '/app.css', '/icon.svg', '/manifest.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith('lazypromotion-preview-shell-') && key !== CACHE) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.search || !SHELL.includes(url.pathname)) return;
  event.respondWith((async () => {
    try { return await fetch(event.request); }
    catch { return await caches.match(event.request) || Response.error(); }
  })());
});
