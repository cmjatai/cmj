if (workbox) {
  workbox.core.setCacheNameDetails({prefix: "frontend"});
  self.__precacheManifest = [{
    url: '/offline/',
    revision: 'abcde'
  }].concat(self.__precacheManifest || []);
  
  workbox.precaching.suppressWarnings();
  
  workbox.precaching.precacheAndRoute(
    self.__precacheManifest, 
    {
      offlinePage: '/offline/', //<- in case of getting offline and not have cache content , redirect here
    }
  );
  
  console.log('self.__precacheManifest:')
  console.log(self.__precacheManifest)

} 
else {
  console.log(`Workbox didn't load`);
}

