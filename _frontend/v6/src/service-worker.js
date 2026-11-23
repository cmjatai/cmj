import { precacheAndRoute } from 'workbox-precaching'

precacheAndRoute(self.__WB_MANIFEST)

// Versão do build (docs/specs/infra/versionamento.md): muda o arquivo a cada build.
// eslint-disable-next-line no-undef
self.PORTALCMJ_VERSAO = __PORTALCMJ_VERSAO__

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

