<template>
  <div class="cmj-component-json-viewer">
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
import Utils from '~@/js/resources'
import { useMessageStore } from '~@/js/stores/MessageStore'

const messageStore = useMessageStore()

const props = defineProps({
  identify: {
    type: String,
    required: true,
  },
  editable: {
    type: Boolean,
    default: false,
  },
  deep: {
    type: Number,
    default: 3,
  },
  objectid: {
    type: Number,
    required: true,
  },
})

const jdata_initial = JSON.parse(document.getElementById(props.identify).textContent);
const jdata_string = JSON.stringify(jdata_initial, null, 2);

const state = reactive({
  val: jdata_string,
  log: '',
  data: jdata_initial,
  showLine: true,
  showLineNumber: false,
  editable: props.editable,
  editableTrigger: 'click',
  deep: props.deep,
});

const sendJData = (jdata) => {
  try {
    const formData = new FormData();
      formData.append('jdata', JSON.stringify(jdata));

      Utils.Utils.patchModel('etl', 'layout', props.objectid, formData)
        .then((response) => {
          if (response.status === 200) {
            messageStore.addMessage({
              type: 'success',
              text: `Layout Atualizado: ${response.data.nome}`,
              timeout: 5000
            })
            if (response.data.response_message !== undefined) {
              state.log = `Layout Atualizado: ${response.data.nome}\n\n${response.data.response_message}`;
            }
            else {
              state.log = `Layout Atualizado: ${response.data.nome}`;
            }
          } else {
            console.error('Error saving JSON:', response.statusText);
          }
        })
        .catch((error) => {
          state.log = error.response.data.jdata[0];
        }
      )
  } catch {
    state.log = 'Erro: Sintaxe JSON inválida.';
  }
}

// watch(
//   () => state.val,
//   newVal => {
//     try {
//       state.data = JSON.parse(newVal);
//       //console.log('state val');
//     } catch {
//       // console.log('JSON ERROR');
//     }
//   },
// );


watch(
  () => state.data,
  newVal => {
    try {
      sendJData(newVal);
      state.val = JSON.stringify(newVal, null, 2);
    } catch  {
      state.log = 'Erro: Sintaxe JSON inválida.';
    }
  },
);

const changeTextarea = () => {
  try {
    state.data = JSON.parse(state.val);
  } catch {
    state.log = 'Erro: Sintaxe JSON inválida.';
  }
}

</script>
<style scoped>
.cmj-component-json-viewer {

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
  zoom: 1.3
}
</style>
