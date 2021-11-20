import { createApp } from '~/main'
import type { PageContext } from './types'

const pageContext: PageContext = {
  documentProps: {
    title: 'V3 Project'
  }
}
const { app, router } = createApp(pageContext)

// wait until router is ready before mounting to ensure hydration match
router.isReady().then(async () => {
  if (import.meta.env.PROD)
    await import('./pwa')
  app.mount('#app')

})
