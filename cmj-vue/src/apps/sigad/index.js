import Vue from 'vue'
import DocumentoEdit from './components/DocumentoEdit'
import Container from './components/Container'
import ContainerFluid from './components/ContainerFluid'

Vue.component('DocumentoEdit', DocumentoEdit)
Vue.component('Container', Container)
Vue.component('ContainerFluid', ContainerFluid)

export default {
  DocumentoEdit,
  Container,
  ContainerFluid
}
