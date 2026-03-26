<template>
  <div
    class="drop_files"
    @drop.prevent="dropHandler"
    @dragover.prevent
    @dragend="dragendHandler"
  >
    <div
      class="progress"
      :style="`width: ${progress}`"
    />
    <label
      class="drop_zone"
      for="input_file_dropzone"
    >
      <span
        class="inner"
        v-if="multiple"
      >
        Arraste seus arquivos e solte aqui,<br>
        <small>ou clique para selecionar</small>
      </span>
      <span
        class="inner"
        v-if="!multiple"
      >
        Arraste seu arquivo e solte aqui,<br>
        <small>ou clique para selecionar</small>
      </span>
      <input
        :multiple="multiple || null"
        type="file"
        name="file"
        id="input_file_dropzone"
        @change="selectFiles"
      >
    </label>
    <div class="view">
      <img
        :src="srcLocal"
        v-if="src"
      >
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'

const messageStore = useMessageStore()

const props = defineProps({
  src: { type: String, default: '' },
  multiple: { type: Boolean, default: false },
  pk: { type: [Number, String], required: true }
})

const emit = defineEmits(['uploaded'])

const srcLocal = ref(props.src)
const progress = ref('0%')

watch(() => props.src, (nv) => {
  srcLocal.value = nv
})

function selectFiles (ev) {
  const files = ev.currentTarget.files
  if (files.length === 0) return
  sendFiles(files)
}

function sendFiles (files) {
  const form = new FormData()
  for (let i = 0; i < files.length; i++) {
    form.append('arquivos', files[i])
    form.append('lastmodified', files[i].lastModified)
  }
  Resources.Utils.postModel({
    app: 'arq',
    model: 'draft',
    action: `${props.pk}/uploadfiles`,
    form,
    progress: {
      onUploadProgress: (event) => {
        const _progress = Math.round((event.loaded * 100) / event.total)
        progress.value = `${_progress}%`
      }
    }
  })
    .then((response) => {
      progress.value = '0%'
      srcLocal.value = props.src + '?' + Date.now()
      emit('uploaded', response)
      messageStore.addMessage({ type: 'success', text: 'Envio de Arquivos concluído...', timeout: 5000 })
    })
    .catch((response) => {
      messageStore.addMessage({
        type: 'danger',
        text: response.response?.data?.[0] || response.response?.data?.detail || 'Não foi possível enviar os arquivos...',
        timeout: 10000
      })
    })
}

function dropHandler (ev) {
  const dt = ev.dataTransfer
  sendFiles(dt.files)
}

function dragendHandler (ev) {
  const dt = ev.dataTransfer
  if (dt.items) {
    for (let i = 0; i < dt.items.length; i++) {
      dt.items.remove(i)
    }
  } else {
    ev.dataTransfer.clearData()
  }
}
</script>

<style lang="scss">
.drop_files {
  width: 100%;
  text-align: center;
  background: transparentize(#fff, 0.5);
  position: relative;
  min-height: 120px;
  border: 3px dashed #cccfcc;
  .progress {
    background: #3390fa;
    line-height: 7px;
    height: 7px;
  }
  input {
    visibility: hidden;
    position: fixed;
    top: -100px;
    left: -100px;
    height: 0px;
    width: 0px;
  }
}
.drop_zone {
  cursor: pointer;
  position: absolute;
  line-height: 1;
  margin: 0;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: transparentize(#fff, 0.5);
  opacity: 0.5;
  span {
    color: black;
    small {
      color: #000080;
    }
  }
  &:hover {
    opacity: 1;
  }
}
</style>
