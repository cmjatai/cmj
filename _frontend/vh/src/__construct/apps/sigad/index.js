import Vue from 'vue'
import DocumentoEdit from './components/DocumentoEdit'

import Container from './components/Container'
import ContainerFile from './components/ContainerFile'
import ContainerFluid from './components/ContainerFluid'
import ContainerTdBi from './components/ContainerTdBi'

import TpdTexto from './components/TpdTexto'
import TpdFile from './components/TpdFile'
import TpdVideo from './components/TpdVideo'
import TpdAudio from './components/TpdAudio'
import TpdImage from './components/TpdImage'
import TpdImageTdBi from './components/TpdImageTdBi'
import ModalImageList from './components/ModalImageList'
import TpdGallery from './components/TpdGallery'
import TpdReferencia from './components/TpdReferencia'
import ModalReferenciaImageList from './components/ModalReferenciaImageList'

Vue.component('DocumentoEdit', DocumentoEdit)
Vue.component('Container', Container)
Vue.component('ContainerFluid', ContainerFluid)
Vue.component('ContainerFile', ContainerFile)
Vue.component('TpdTexto', TpdTexto)
Vue.component('TpdFile', TpdFile)
Vue.component('TpdVideo', TpdVideo)
Vue.component('TpdAudio', TpdAudio)
Vue.component('TpdImage', TpdImage)
Vue.component('ContainerTdBi', ContainerTdBi)
Vue.component('TpdImageTdBi', TpdImageTdBi)
Vue.component('ModalImageList', ModalImageList)
Vue.component('TpdGallery', TpdGallery)
Vue.component('TpdReferencia', TpdReferencia)
Vue.component('ModalReferenciaImageList', ModalReferenciaImageList)

export default {
  DocumentoEdit,
  Container,
  ContainerFluid,
  ContainerFile,
  TpdTexto,
  TpdFile,
  TpdVideo,
  TpdAudio,
  TpdImage,
  ContainerTdBi,
  TpdImageTdBi,
  ModalImageList,
  TpdGallery,
  TpdReferencia,
  ModalReferenciaImageList
}
