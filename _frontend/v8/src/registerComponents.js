
import App from './App.vue'
import { defineAsyncComponent } from 'vue'

// cmj = PortalCMJ Frontend

const rootComponents = {
  // Para ser utilizado em templates Django se não estiver em globalComponents.
  'cmj-app': App,
  'cmj-error-404': defineAsyncComponent(() => import('~@/views/Error404.vue'))
}

const globalComponents = {

}

export default {
  rootComponents,
  globalComponents
}
