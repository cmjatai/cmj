import StoreSigad from './sigad/store'
import StoreUtils from './utils/store'

export default {
  modules: {
    sigad__documento_edit: StoreSigad.StoreDocumentoEdit,
    utils__message: StoreUtils.StoreMessage
  }
}
