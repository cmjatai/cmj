import Vue from 'vue'
import DocumentoEdit from './components/DocumentoEdit'
import Container from './components/Container'
import ContainerFluid from './components/ContainerFluid'
import TpdTexto from './components/TpdTexto'

Vue.component('DocumentoEdit', DocumentoEdit)
Vue.component('Container', Container)
Vue.component('ContainerFluid', ContainerFluid)
Vue.component('TpdTexto', TpdTexto)

export default {
  DocumentoEdit,
  Container,
  ContainerFluid,
  TpdTexto
}
