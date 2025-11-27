import '../../expose-global-jquery'
import './scss/loa.scss'
import axios from 'axios'
import AppLOA from './AppLOA'

axios.defaults.headers.get['Cache-Control'] = 'no-cache, no-store, must-revalidate'
axios.defaults.headers.get['Pragma'] = 'no-cache' // Suporte para navegadores mais antigos
axios.defaults.headers.get['Expires'] = '0' // Expira imediatamente
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

// Inicializa a aplicação LOA quando o documento estiver pronto
$(document).ready(function () {
  if ($('.container-loa').length > 0) {
    AppLOA.run()
  }
})
