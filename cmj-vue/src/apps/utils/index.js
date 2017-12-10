import Vue from 'vue'
import TextareaAutosize from './TextareaAutosize'
import CmjChoices from './CmjChoices'
import Message from './Message'
import DropZone from './DropZone'

Vue.component('TextareaAutosize', TextareaAutosize)
Vue.component('CmjChoices', CmjChoices)
Vue.component('Message', Message)
Vue.component('DropZone', DropZone)
export default {
  TextareaAutosize, CmjChoices, Message, DropZone
}
