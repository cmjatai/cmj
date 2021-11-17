import { createApp } from './main'

const { app } = createApp()
app.mount('#app')

// wait until router is ready before mounting to ensure hydration match
//router.isReady().then(() => {
//  app.mount('#app')
//})
