if (workbox) {
  workbox.core.setCacheNameDetails({prefix: "frontend"});
  self.__precacheManifest = [{
    url: '/offline/',
    revision: 'abcde'
  }].concat(self.__precacheManifest || []);
  
  workbox.precaching.suppressWarnings();
  
  workbox.precaching.precacheAndRoute(
    self.__precacheManifest, 
    {}
  );

  workbox.routing.registerRoute(
    ({ event }) => event.request.mode === 'navigate', //if the requests is to go to a new url
    ({ url }) => fetch(url.href,{credentials: 'same-origin'}).catch(() => caches.match('/offline/')) //in case of not match send my to the offline page
  );

  // console.log('self.__precacheManifest:')
  // console.log(self.__precacheManifest)

} 
else {
  console.log(`Workbox didn't load`);
}

