self.addEventListener('install', event => {
  self.skipWaiting(); // Yeni versiyona anında geç
});

self.addEventListener('activate', event => {
  // Eski önbellekleri (cache) tamamen temizle
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          return caches.delete(cache);
        })
      );
    })
  );
  self.clients.claim();
});

// Her zaman en güncel dosyayı internetten çek
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
