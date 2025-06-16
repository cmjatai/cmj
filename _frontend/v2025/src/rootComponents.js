import Error404 from "./views/Error404.vue"
import Alert from "./components/utils/message/Alert.vue"
import App from './App.vue';
import JsonViewer from "./components/utils/JsonViewer.vue";

const rootComponents = {
    'cmj-app': App,
    'cmj-alert': Alert,
    'cmj-error-404': Error404,
    'cmj-json-viewer': JsonViewer,
  }

export default rootComponents
