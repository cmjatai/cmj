import { register } from 'register-service-worker'

const swFile = process.env.NODE_ENV === 'production' ? '/service-worker.js' : '/service-worker.js'

register(swFile, {
  registrationOptions: { scope: '/' },
  ready (registration) {
    console.debug('Service worker is active.')
  },
  registered (registration) {
    console.debug('Service worker has been registered.')
  },
  cached (registration) {
    console.debug('Content has been cached for offline use.')
  },
  updatefound (registration) {
    console.debug('New content is downloading.')
  },
  updated (registration) {
    console.debug('New content is available; please refresh.')
  },
  offline () {
    console.debug('No internet connection found. App is running in offline mode.')
  },
  error (error) {
    console.error('Error during service worker registration:', error)
  }
})
