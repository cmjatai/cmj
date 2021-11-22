import { 
  createStore as _createStore, 
  Store,
  createLogger

} from 'vuex'
import teste from './modules/teste'

const debug = process.env.NODE_ENV !== 'production'

export function createStore(): Store<any> {
  return _createStore({
    modules: {
      teste
    },

    strict: debug,
    plugins: debug ? [createLogger()] : []

  })
}

