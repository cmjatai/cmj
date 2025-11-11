<template>
  <div class="json-viewer">
    <div class="row">
      <div class="col">
        <h4>JSON Viewer</h4>
        <textarea
          v-if="state.editable"
          v-model="state.val"
          @change="changeTextarea"
        />
      </div>
      <div
        class="col-6"
        v-if="state.editable"
      >
        <h4>Log de Atualização</h4>
        <markdown
          :source="state.log"
          class="log-jdata-change"
        />
      </div>
    </div>
    <vue-json-pretty
      v-model:data="state.data"
      :deep="state.deep"
      :show-double-quotes="true"
      :show-line="state.showLine"
      :show-line-number="state.showLineNumber"
      :editable="state.editable"
      :editable-trigger="state.editableTrigger"
    >
      <template #renderNodeValue="{ node, defaultValue }">
        <template v-if="typeof node.content === 'string' && node.content.startsWith('http')">
          <a
            :href="node.content"
            target="_blank"
          >{{ node.content }}</a>
        </template>
        <template v-else>
          {{ defaultValue }}
        </template>
      </template>
    </vue-json-pretty>
  </div>
</template>

<script setup>
import { reactive, watch, defineProps } from 'vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

import Markdown from './Markdown.vue'
import Resource from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'

const messageStore = useMessageStore()

const props = defineProps({
  editable: {
    type: Boolean,
    default: false
  },
  deep: {
    type: Number,
    default: 5
  },
  app: {
    type: String,
    required: true
  },
  model: {
    type: String,
    required: true
  },
  objectId: {
    type: Number,
    required: true
  },
  fieldName: {
    type: String,
    required: true
  },
  jsonString: {
    type: String,
    default: ''
  },
  jsonValue: {
    type: Object,
    default: () => ({})
  }
})

const state = reactive({
  val: props.jsonString,
  log: '',
  data: props.jsonValue,
  showLine: true,
  showLineNumber: false,
  editable: props.editable,
  editableTrigger: 'click',
  deep: props.deep
})

const sendJData = (jdata) => {
  try {
    const form = new FormData()
      form.append(props.fieldName, JSON.stringify(jdata))

      Resource.Utils.patchModel({
        app: props.app,
        model: props.model,
        id: props.objectId,
        form: form
      })
        .then((response) => {
          if (response.status === 200) {
            messageStore.addMessage({
              type: 'success',
              text: 'JSON Atualizado:',
              timeout: 5000
            })
          }
        })
        .catch((error) => {
          state.log = `Erro ao atualizar JSON: ${error}`
        }
      )
  } catch {
    state.log = 'Erro: Sintaxe JSON inválida.'
  }
}

watch(
  () => state.data,
  newVal => {
    try {
      sendJData(newVal)
      state.val = JSON.stringify(newVal, null, 2)
    } catch  {
      state.log = 'Erro: Sintaxe JSON inválida.'
    }
  },
  { deep: true }
)

const changeTextarea = () => {
  try {
    state.data = JSON.parse(state.val)
  } catch {
    state.log = 'Erro: Sintaxe JSON inválida.'
  }
}

</script>
<style lang="scss" scoped>
.json-viewer {
  textarea {
    width: 100%;
    height: 55vh;
    font-size: 1rem;
    font-family: 'Courier New', Courier, monospace;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #ccc;
  }

  .log-jdata-change {
    height: 55vh;
    overflow-y: auto;
    border: 1px solid #ccc;
    border-radius: 0.5rem;
    padding: 0.5rem;
  }

}
.vjs-tree {
  padding: 0.5rem;
  zoom: 1.3;
}
</style>
