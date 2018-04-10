import Vue from 'vue'
import App from '../App'
import Loading from './utils/Loading'

import Endereco from './cmj/vuetest/Endereco'
import Endereco2 from './cmj/vuetest/Endereco2'

Vue.component('Loading', Loading)
Vue.component('Endereco', Endereco)
Vue.component('Endereco2', Endereco2)


export default {
  Loading,
  Endereco,
  Endereco2,
  App
}
