importScripts("/static/precache-manifest.21c9b5f8d8a1b309c3cedfa58a8533a2.js", "https://storage.googleapis.com/workbox-cdn/releases/4.3.1/workbox-sw.js");

/* eslint-disable no-undef */
if (workbox) {
  workbox.core.setCacheNameDetails({ prefix: 'frontend' })
  self.__precacheManifest = [{
    url: '/offline/',
    revision: '000005'
  }].concat(self.__precacheManifest || [])

  workbox.precaching.precacheAndRoute(self.__precacheManifest, {})

  // workbox.routing.registerRoute(
  //  ({ event }) => event.request.mode === 'navigate', //if the requests is to go to a new url
  //  ({ url }) => fetch(url.href,{credentials: 'same-origin'}).catch(() => caches.match('/offline/')) //in case of not match send my to the offline page
  // );

  // console.log('self.__precacheManifest:')
  // console.log(self.__precacheManifest)
} else {
  // console.log(`Workbox didn't load`)
}

