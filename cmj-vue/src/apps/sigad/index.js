import Vue from 'vue'
import DocumentoEdit from './components/DocumentoEdit'

import Container from './components/Container'
import ContainerFluid from './components/ContainerFluid'
import ContainerTdBi from './components/ContainerTdBi'

import TpdTexto from './components/TpdTexto'
import TpdVideo from './components/TpdVideo'
import TpdAudio from './components/TpdAudio'
import TpdImage from './components/TpdImage'
import TpdImageTdBi from './components/TpdImageTdBi'
import ModalImageList from './components/ModalImageList'
import TpdGallery from './components/TpdGallery'

Vue.component('DocumentoEdit', DocumentoEdit)
Vue.component('Container', Container)
Vue.component('ContainerFluid', ContainerFluid)
Vue.component('TpdTexto', TpdTexto)
Vue.component('TpdVideo', TpdVideo)
Vue.component('TpdAudio', TpdAudio)
Vue.component('TpdImage', TpdImage)
Vue.component('ContainerTdBi', ContainerTdBi)
Vue.component('TpdImageTdBi', TpdImageTdBi)
Vue.component('ModalImageList', ModalImageList)
Vue.component('TpdGallery', TpdGallery)

export default {
  DocumentoEdit,
  Container,
  ContainerFluid,
  TpdTexto,
  TpdVideo,
  TpdAudio,
  TpdImage,
  ContainerTdBi,
  TpdImageTdBi,
  ModalImageList,
  TpdGallery
}
