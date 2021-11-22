import '@/assets/scss/app.scss'

import { createApp } from './main'
import type { PageContext } from './types'

const pageContext: PageContext = {
  documentProps: {
    title: 'V3 Project' 
  }
}
const { app, router, store } = createApp(pageContext)

if (window.__INITIAL_STATE__) {
  store.replaceState(window.__INITIAL_STATE__)
  delete window.__INITIAL_STATE__
}
router.isReady().then(async () => {
  if (import.meta.env.PROD)
    await import('./pwa')
  app.mount('#app')

})
