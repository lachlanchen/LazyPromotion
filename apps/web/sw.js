// Only the fixed public client shell is cached. API data needs an explicit save.
const CACHE = 'lazypromotion-preview-shell-v2';
const SHELL = ['/', '/app.mjs', '/model.mjs', '/draft-model.mjs', '/draft-ui.mjs', '/app.css', '/icon.svg', '/manifest.webmanifest'];
self.addEventListener('install', event => {
  // The complete shell is available before taking over. There are no queued
  // network actions to replay; in-progress drafts remain in the page's memory.
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('message', event => {
  if (event.data === 'shell-version' && event.ports[0]) event.ports[0].postMessage(CACHE);
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
