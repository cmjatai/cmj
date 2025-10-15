
import Alert from '~@/components/atoms/Alert.vue'
import App from './App.vue'
import RefreshPage from '~@/components/atoms/RefreshPage.vue'

// cmj = PortalCMJ Frontend
const Error404 = () => import('~@/views/Error404.vue')

const rootComponents = {
    'cmj-app': App,
    'cmj-alert': Alert,
    'cmj-error-404': Error404,
    'cmj-refresh-page': RefreshPage,
  }

export default rootComponents
