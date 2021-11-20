import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { clientsClaim } from 'workbox-core'
import { ManifestEntry } from 'workbox-build'

cleanupOutdatedCaches()

declare let self: ServiceWorkerGlobalScope

const manifest = self.__WB_MANIFEST as Array<ManifestEntry>
precacheAndRoute(manifest)
//console.log(manifest)

self.skipWaiting()
clientsClaim()