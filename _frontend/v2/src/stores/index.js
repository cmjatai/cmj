import StoreMessage from './message/StoreMessage'
import StoreOnline from './online/StoreOnline'

export default {
  modules: {
    store__message: StoreMessage,
    store__online: StoreOnline
  },
  strict: process.env.NODE_ENV === 'production'
}
