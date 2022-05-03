import StoreMessage from './message/StoreMessage'
import StoreOnline from './online/StoreOnline'
import StoreDocumentoEdit from './sigad/StoreDocumentoEdit'

export default {
  modules: {
    store__message: StoreMessage,
    store__online: StoreOnline,
    store__documento_edit: StoreDocumentoEdit
  },
  strict: process.env.NODE_ENV === 'production'
}
