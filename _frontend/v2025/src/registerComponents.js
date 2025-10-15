
import App from './App.vue'
import { defineAsyncComponent } from 'vue'

// cmj = PortalCMJ Frontend

const rootComponents = {
  // Para ser utilizado em templates Django se não estiver em globalComponents.
  'cmj-app': App,
  'cmj-error-404': defineAsyncComponent(() => import('~@/views/Error404.vue'))
}

const globalComponents = {
  // Para ser utilizado em qualquer componente Vue sem necessidade de importação.
  // O colocado em globalComponents não precisa ser colocado em rootComponents.
  'cmj-refresh-page': defineAsyncComponent(() => import('~@/components/atoms/RefreshPage.vue')),
  'cmj-alert': defineAsyncComponent(() => import('~@/components/atoms/Alert.vue'))
}

export default {
  rootComponents,
  globalComponents
}
