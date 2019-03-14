import Vue from 'vue'
import TextareaAutosize from './TextareaAutosize'
import CmjChoices from './CmjChoices'
import Message from './Message'
import DropZone from './DropZone'
import Modal from './Modal'

Vue.component('TextareaAutosize', TextareaAutosize)
Vue.component('CmjChoices', CmjChoices)
Vue.component('Message', Message)
Vue.component('DropZone', DropZone)
Vue.component('Modal', Modal)
export default {
  TextareaAutosize, CmjChoices, Message, DropZone, Modal
}
