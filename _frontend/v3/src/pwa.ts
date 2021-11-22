import { registerSW } from 'virtual:pwa-register'

console.log('pwa: isReady from router.ts')

const updateSW = registerSW({
    onNeedRefresh() {
        console.log('on neek refresh')
    },
    onOfflineReady() {
        console.log('on offlineRead')
    },
    onRegistered(registration: ServiceWorkerRegistration | undefined) {
        console.log('pwa: isReady from router.ts - onRegistred')
        //console.log(registration)
    }
})
