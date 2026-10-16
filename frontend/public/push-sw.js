// Service Worker adicional para manejo de Notificaciones Push (Práctica 2.1)

self.addEventListener('push', (event) => {
  let payload = {
    title: '🛡️ ModeraciónApp - Alerta Push',
    body: 'Se ha recibido una nueva actualización en la plataforma de moderación.',
    icon: '/pwa-192x192.png',
    badge: '/pwa-192x192.png',
    tag: 'moderacion-push',
    data: {
      url: '/',
      timestamp: Date.now(),
    },
  };

  if (event.data) {
    try {
      const parsed = event.data.json();
      payload = {
        ...payload,
        ...parsed,
      };
    } catch {
      payload.body = event.data.text();
    }
  }

  const options = {
    body: payload.body,
    icon: payload.icon || '/pwa-192x192.png',
    badge: payload.badge || '/pwa-192x192.png',
    tag: payload.tag || 'moderacion-push',
    vibrate: [200, 100, 200],
    requireInteraction: false,
    data: payload.data || { url: '/', timestamp: Date.now() },
    actions: [
      { action: 'open', title: 'Abrir Plataforma' },
      { action: 'dismiss', title: 'Descartar' },
    ],
  };

  event.waitUntil(self.registration.showNotification(payload.title, options));
});

// Escuchar mensajes desde la aplicación cliente para disparar notificaciones desde el SW
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_PUSH_NOTIFICATION') {
    const { title, body, tag, data } = event.data.payload || {};
    const notificationTitle = title || '🛡️ ModeraciónApp - Notificación Push';
    const options = {
      body: body || 'Notificación push de prueba enviada desde el Service Worker.',
      icon: '/pwa-192x192.png',
      badge: '/pwa-192x192.png',
      tag: tag || `moderacion-test-${Date.now()}`,
      vibrate: [200, 100, 200],
      data: data || { url: '/', timestamp: Date.now() },
      actions: [
        { action: 'open', title: 'Ver en App' },
        { action: 'dismiss', title: 'Cerrar' },
      ],
    };

    event.waitUntil(self.registration.showNotification(notificationTitle, options));
  }
});

// Manejo de clic sobre la notificación push
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const targetUrl = (event.notification.data && event.notification.data.url) || '/';

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) {
            client.postMessage({
              type: 'NOTIFICATION_CLICKED',
              payload: {
                title: event.notification.title,
                action: event.action || 'default',
                timestamp: Date.now(),
              },
            });
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl);
        }
      })
  );
});
