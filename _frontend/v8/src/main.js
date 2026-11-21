import 'vite/modulepreload-polyfill'

import '~@/css/app.css'

import { iniciar } from '~@/core/boot'

iniciar()

// Registro manual do Service Worker para controle total da URL
console.debug('Environment Mode:', import.meta.env.MODE)

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  const swUrl = '/v8/service-worker.js'

  navigator.serviceWorker.register(swUrl, { scope: '/v8/' , type: 'module' })
    .then((registration) => {
      console.debug('Service Worker registrado com sucesso no escopo:', registration.scope)
    })
    .catch((error) => {
      console.error('Falha ao registrar o Service Worker:', error)
    })
}
