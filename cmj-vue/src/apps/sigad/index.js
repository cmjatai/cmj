import Vue from 'vue'
import DocumentoEdit from './components/DocumentoEdit'
import Container from './components/Container'
import ContainerFluid from './components/ContainerFluid'
import TpdTexto from './components/TpdTexto'
import TpdVideo from './components/TpdVideo'
import TpdAudio from './components/TpdAudio'
import TpdImage from './components/TpdImage'

Vue.component('DocumentoEdit', DocumentoEdit)
Vue.component('Container', Container)
Vue.component('ContainerFluid', ContainerFluid)
Vue.component('TpdTexto', TpdTexto)
Vue.component('TpdVideo', TpdVideo)
Vue.component('TpdAudio', TpdAudio)
Vue.component('TpdImage', TpdImage)

export default {
  DocumentoEdit,
  Container,
  ContainerFluid,
  TpdTexto,
  TpdVideo,
  TpdAudio,
  TpdImage
}
