/* eslint-disable no-useless-return */
/* eslint-disable no-undef */
import { precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { NetworkOnly } from 'workbox-strategies'

precacheAndRoute(self.__WB_MANIFEST)

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
           url.pathname.startsWith('/v2026') ||
           url.pathname.startsWith('/dash')
  },
  new NetworkOnly()
)
