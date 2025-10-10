import StoreAuth from './stores/auth/StoreAuth'
import StoreMessage from './stores/message/StoreMessage'
import StoreOnline from './stores/online/StoreOnline'
import syncStore from './stores/sync/sync'

export default {
  modules: {
    store__auth: StoreAuth,
    store__message: StoreMessage,
    store__online: StoreOnline,
    store__sync: syncStore
  },
  strict: process.env.NODE_ENV === 'production'
}
