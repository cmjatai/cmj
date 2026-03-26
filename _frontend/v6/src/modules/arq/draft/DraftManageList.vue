<template>
  <div class="draftmanagelist">
    <div class="row">
      <div class="col d-flex grade">
        <div class="btn-group">
          <button
            class="btn"
            title="Atualizar lista"
            @click="drawList(0)"
          >
            <FontAwesomeIcon icon="sync-alt" />
          </button>
        </div>
        <div class="d-flex grade">
          <BFormSpinbutton
            id="spincols"
            v-model="cols"
            min="1"
            max="12"
            inline
          />
          <BFormSpinbutton
            id="spinrows"
            v-model="rows"
            min="1"
            max="100"
            inline
          />
        </div>
        <Pagination
          :pagination="pagination"
          :page-size="rows * cols"
          @next-page="nextPage"
          @previous-page="previousPage"
          @current-page="currentPage"
        />
        <div
          v-if="draftselected"
          class="btn-toolbar"
          role="toolbar"
          aria-label="Toolbar with button groups"
        >
          <a
            class="btn btn-danger"
            title="Excluir Draft Atual"
            @click="clickDel"
            :disabled="draftselected === null"
          >
            <FontAwesomeIcon icon="trash-alt" />
          </a>
          <a
            class="btn btn-warning text-white ms-2"
            @click="clickSupendeConversao"
            title="Cancela agendamentos de conversão de PDF -> PDF/A-2b"
          >
            <FontAwesomeIcon icon="stop-circle" />
          </a>
          <a
            class="btn btn-primary ms-2 btn-pdf2pdfa"
            @click="clickPdf2Pdfa"
            title="Iniciar conversão Básica para PDF/A-2b de todos os arquivos do Draft selecionado."
          >
            <span>PDF -><br>PDF/A-2b</span>
          </a>
          <a
            class="btn btn-primary ms-2"
            :href="`/api/arq/draft/${draftselected.id}/zipfile/?t=${Date.now()}`"
            target="_blank"
            rel="noopener noreferrer"
            title="Baixar todos os arquivos individualmente dentro de um arquivo compactado."
          >
            <FontAwesomeIcon icon="file-archive" />
          </a>
          <a
            class="btn btn-primary ms-2"
            @click="clickUnir"
            title="Unir PDFs do Draft em apenas um PDF"
          >
            <FontAwesomeIcon icon="layer-group" />
          </a>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <DraftMidia
          :elemento="item"
          :cols="cols"
          v-for="(item, k) in draftmidialistOrdered"
          :key="`dm${k}`"
          @redraw-draft-midia="drawList(-1)"
          @update-element="updateElement"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import DraftMidia from './DraftMidia.vue'
import Pagination from '~@/components/atoms/Pagination.vue'

const messageStore = useMessageStore()

const props = defineProps({
  draftselected: { type: Object, default: null }
})

const emit = defineEmits(['reloadDrafts'])

const pagination = ref({})
const draftmidialist = ref({})
const cols = ref(4)
const rows = ref(3)

const draftmidialistOrdered = computed(() => {
  return [...Object.values(draftmidialist.value)].sort((a, b) => a.sequencia - b.sequencia)
})

watch(() => props.draftselected, (nw) => {
  fetchMidias(nw)
})

watch(rows, () => {
  fetchMidias(props.draftselected)
})

watch(cols, () => {
  fetchMidias(props.draftselected)
})

function clickUnir () {
  Resources.Utils.patchModel({
    app: 'arq',
    model: 'draft',
    id: props.draftselected.id,
    action: 'unirmidias'
  })
    .then(() => fetchMidias(props.draftselected))
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function clickSupendeConversao () {
  Resources.Utils.patchModel({
    app: 'arq',
    model: 'draft',
    id: props.draftselected.id,
    action: 'cancela_pdf2pdfa'
  })
    .then(() => fetchMidias(props.draftselected))
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function clickPdf2Pdfa () {
  Resources.Utils.patchModel({
    app: 'arq',
    model: 'draft',
    id: props.draftselected.id,
    action: 'pdf2pdfa'
  })
    .then(() => fetchMidias(props.draftselected))
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function clickDel () {
  Resources.Utils.deleteModel({
    app: 'arq',
    model: 'draft',
    id: props.draftselected.id
  })
    .then(() => emit('reloadDrafts'))
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function drawList (value) {
  const l = Object.keys(draftmidialist.value).length
  if (value === -1) {
    fetchMidias(props.draftselected, l > 1 ? pagination.value.page : (pagination.value.previous_page || 1))
  } else {
    fetchMidias(props.draftselected, l > 0 ? pagination.value.page : (pagination.value.previous_page || 1))
  }
}

function changeMatriz () {
  const dm = document.getElementsByClassName('draft-midia')
  Array.from(dm).forEach((item) => {
    item.style.maxWidth = `${100 / cols.value}%`
    item.style.flex = `0 0 ${100 / cols.value}%`
  })
}

function currentPage (value) {
  if (value !== null && value >= 0) {
    fetchMidias(props.draftselected, value)
  }
}

function updateElement (el) {
  draftmidialist.value[el.id] = el
}

function nextPage () {
  fetchMidias(props.draftselected, pagination.value.next_page)
}

function previousPage () {
  fetchMidias(props.draftselected, pagination.value.previous_page)
}

function fetchMidias (draft, page = 1) {
  if (draft !== null && draft?.id > 0) {
    draftmidialist.value = {}
    nextTick(() => {
      Resources.Utils.fetch({
        app: 'arq',
        model: 'draftmidia',
        query_string: `o=sequencia&page=${page}&draft=${draft.id}&page_size=${rows.value * cols.value}`
      })
        .then((response) => {
          pagination.value = response.data.pagination
          const results = response.data.results || response.data
          results.forEach((item) => {
            draftmidialist.value[item.id] = item
          })
        })
        .then(() => changeMatriz())
        .catch(() => {
          messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar a lista...', timeout: 5000 })
        })
    })
  } else {
    draftmidialist.value = {}
  }
}

onMounted(() => {
  changeMatriz()
})

defineExpose({ fetchMidias })
</script>

<style lang="scss">
.draftmanagelist {
  .grade {
    gap: 1em;
  }
  .b-form-spinbutton {
    output {
      padding: 0 10px;
    }
  }
  .widget-pagination {
    flex: 1 1 auto;
  }
  .btn-pdf2pdfa {
    font-size: 10px;
    line-height: 1;
    display: flex;
    align-items: center;
    padding: 3px;
  }
}
</style>
