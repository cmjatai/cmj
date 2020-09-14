importScripts("/static/precache-manifest.33ba0e58685b2b2e15038bc89ba00d03.js", "https://storage.googleapis.com/workbox-cdn/releases/3.6.3/workbox-sw.js");

if (workbox) {
  workbox.core.setCacheNameDetails({prefix: "frontend"})
  self.__precacheManifest = [{
    url: '/offline/',
    revision: '000002'
  }].concat(self.__precacheManifest || [])
  
  workbox.precaching.suppressWarnings()
  
  workbox.precaching.precacheAndRoute(self.__precacheManifest, {})

  //workbox.routing.registerRoute(
  //  ({ event }) => event.request.mode === 'navigate', //if the requests is to go to a new url
  //  ({ url }) => fetch(url.href,{credentials: 'same-origin'}).catch(() => caches.match('/offline/')) //in case of not match send my to the offline page
  //);

  // console.log('self.__precacheManifest:')
  // console.log(self.__precacheManifest)

} 
else {
  console.log(`Workbox didn't load`)
}


