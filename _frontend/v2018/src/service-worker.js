/* eslint-disable no-useless-return */
/* eslint-disable no-undef */
import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { NetworkOnly } from 'workbox-strategies'

precacheAndRoute(self.__WB_MANIFEST)

// Versão do build (docs/specs/infra/versionamento.md): muda o arquivo a cada build.
self.PORTALCMJ_VERSAO = __PORTALCMJ_VERSAO__

// Ativa assim que instalado e assume as páginas abertas, como os SWs do v6 e do v8.
self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('message', (event) => {
  console.debug('SW received message:', event.data)
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting()
  }
})

// Exclude specific routes from SW handling (NetworkOnly)
// This ensures the SW just passes these requests to the network
registerRoute(
  ({ url }) => {
    console.debug('SW checking URL:', url.pathname)
    return url.pathname.startsWith('/api') ||
           url.pathname.startsWith('/admin') ||
           url.pathname.startsWith('/v6') ||
           url.pathname.startsWith('/dash')
  },
  new NetworkOnly()
)
