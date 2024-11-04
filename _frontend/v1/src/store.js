import StoreAuth from './stores/auth/StoreAuth'
import StoreMessage from './stores/message/StoreMessage'
import StoreOnline from './stores/online/StoreOnline'

export default {
  modules: {
    store__auth: StoreAuth,
    store__message: StoreMessage,
    store__online: StoreOnline
  },
  strict: process.env.NODE_ENV === 'production'
}
