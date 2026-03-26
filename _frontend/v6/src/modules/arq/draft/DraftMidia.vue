<template>
  <div
    :class="['draft-midia', 'p-2']"
    :id="`dm${elemento.id}`"
  >
    <div
      class="inner"
      @mouseenter="enterInner"
      @mouseleave="leaveInner"
    >
      <div
        :class="['inner-status', statusClass]"
        v-html="statusText"
      />
      <div
        class="inner-action"
        ref="inneractionRef"
      >
        <div
          class="dropstart"
          ref="dropleftRef"
          v-show="elemento.metadata.ocrmypdf.pdfa !== 10"
        >
          <button
            class="btn btn-sm"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            ref="btnDropDownActionsRef"
          >
            <FontAwesomeIcon icon="ellipsis-v" />
          </button>
          <div
            class="dropdown-menu"
            ref="dropdownRef"
          >
            <a
              class="dropdown-item"
              title="PDF -> PDF/A-2b - Conversão rápida, pode não ser feita devido a erros no arquivo."
              @click="clickDraftmidiaAction('pdf2pdfa_rapida')"
            >
              PDF -> PDF/A-2b (Conversão Rápida)
            </a>
            <a
              class="dropdown-item"
              title="PDF -> PDF/A-2b - Conversão básica, pode demorar um pouco mais que a rápida por aplicar correção de possíveis erros no arquivo. Utilize caso a rápida tenha falhado."
              @click="clickDraftmidiaAction('pdf2pdfa_basica')"
            >
              PDF -> PDF/A-2b (Conversão Básica)
            </a>
            <a
              class="dropdown-item"
              title="PDF -> PDF/A-2b - Conversão forçada, faz OCR e é mais lenta que a básica. (útil para arquivos digitalizados.)"
              @click="clickDraftmidiaAction('pdf2pdfa_forcada')"
            >
              PDF -> PDF/A-2b (Conversão Forçada)
            </a>
            <a
              class="dropdown-item"
              title="PDF -> PDF/A-2b - Conversão Compacta, faz OCR, converte para preto e branco e aplica alta compactação no arquivo (ultra lenta e útil para arquivos digitalizados)."
              @click="clickDraftmidiaAction('pdf2pdfa_compacta')"
            >
              PDF -> PDF/A-2b (Conversão de Alta Compactação)
            </a>
            <a
              class="dropdown-item"
              title="Gerar um PDF para cada página"
              @click="clickDraftmidiaAction('decompor')"
            >
              Decompor <FontAwesomeIcon icon="expand" />
            </a>
            <a
              class="dropdown-item"
              title="Apagar Mídia"
              @click="clickDel"
            >
              Apagar <FontAwesomeIcon icon="trash-alt" />
            </a>
          </div>
        </div>
      </div>
      <div class="innerimg">
        <a
          :href="elemento.arquivo"
          target="_blank"
        >
          <img
            :src="`${elemento.arquivo}?page=${page}&dpi=48&nocache=${nocache}&u=${data}`"
            ref="imgViewRef"
          >
        </a>
        <div class="img-actions">
          <div v-show="elemento.metadata.uploadedfile.paginas > 1">
            <BFormSpinbutton
              id="spinpages"
              v-model="page"
              min="1"
              :max="elemento.metadata.uploadedfile.paginas"
            />
          </div>
          <button
            class="btn btn-sm btn-outline-primary"
            @click="clickRotate(-90)"
          >
            <FontAwesomeIcon icon="undo" />
          </button>
          <button
            class="btn btn-sm btn-outline-primary"
            @click="clickRotate(90)"
          >
            <FontAwesomeIcon icon="redo" />
          </button>
        </div>
      </div>
      <div class="innerdesc">
        <strong v-html="elemento.metadata.uploadedfile.name" />
        <small v-html="`${elemento.arquivo_size[1]} MB`" />
        <small v-show="elemento.metadata.ocrmypdf.pdfa === 99">PDF/A-2b com OCR</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Dropdown } from 'bootstrap'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'

const messageStore = useMessageStore()

const props = defineProps({
  elemento: { type: Object, required: true },
  cols: { type: Number, default: 4 }
})

const emit = defineEmits(['redrawDraftMidia', 'updateElement'])

const page = ref(1)
const data = ref(Date.now())
const nocache = ref('')

const inneractionRef = ref(null)
const dropleftRef = ref(null)
const btnDropDownActionsRef = ref(null)
const dropdownRef = ref(null)
const imgViewRef = ref(null)

const statusClass = computed(() => {
  const pdfa = props.elemento.metadata.ocrmypdf.pdfa
  if (pdfa === 99) return 'border-green'
  if (pdfa >= 10) return 'border-yellow'
  return 'border-red'
})

const statusText = computed(() => {
  const pdfa = props.elemento.metadata.ocrmypdf.pdfa
  if (pdfa === 99) return 'PDF/A-2b'
  if (pdfa >= 10) return 'Conversão Agendada'
  return 'Não PDF/A-2b'
})

watch(() => props.elemento, () => {
  const estagio = props.elemento.metadata.ocrmypdf.pdfa
  if (estagio >= 10 && estagio <= 20) {
    timeoutUpdate()
  }
})

onMounted(() => {
  nocache.value = ''
  const estagio = props.elemento.metadata.ocrmypdf.pdfa
  if (estagio >= 10 && estagio <= 20) {
    timeoutUpdate()
  }
})

function timeoutUpdate () {
  setTimeout(() => {
    Resources.Utils.fetch({
      app: 'arq',
      model: 'draftmidia',
      id: props.elemento.id
    })
      .then((response) => {
        const estagio = response.data.metadata.ocrmypdf.pdfa
        if (estagio >= 10 && estagio <= 20) {
          timeoutUpdate()
        } else {
          emit('updateElement', response.data)
        }
      })
  }, 5000)
}

function enterInner (ev) {
  const inneraction = inneractionRef.value
  const btnDropDownActions = btnDropDownActionsRef.value
  if (!inneraction || !btnDropDownActions) return
  const rect = ev.currentTarget.getBoundingClientRect()
  inneraction.style.left = `${rect.left + rect.width - btnDropDownActions.offsetWidth - 2}px`
  inneraction.style.top = `${rect.top + 2}px`
}

function leaveInner () {
  if (btnDropDownActionsRef.value) {
    const dd = Dropdown.getInstance(btnDropDownActionsRef.value)
    if (dd) dd.hide()
  }
}

function clickDel () {
  Resources.Utils.deleteModel({
    app: 'arq',
    model: 'draftmidia',
    id: props.elemento.id
  })
    .then(() => emit('redrawDraftMidia'))
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function clickDraftmidiaAction (action) {
  Resources.Utils.patchModel({
    app: 'arq',
    model: 'draftmidia',
    id: props.elemento.id,
    action
  })
    .then(() => {
      data.value = Date.now()
      nocache.value = Date.now()
      nextTick(() => {
        if (imgViewRef.value) {
          imgViewRef.value.src = `${props.elemento.arquivo}?page=${page.value}&dpi=48&nocache=${nocache.value}&u=${data.value}`
        }
        emit('redrawDraftMidia')
      })
    })
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}

function clickRotate (angulo) {
  Resources.Utils.patchModel({
    app: 'arq',
    model: 'draftmidia',
    id: props.elemento.id,
    action: 'rotate',
    progress: { params: { page: page.value, angulo } }
  })
    .then((response) => {
      data.value = Date.now()
      emit('updateElement', response.data)
    })
    .catch((error) => {
      messageStore.addMessage({ type: 'danger', text: error.response.data.message, timeout: 10000 })
    })
}
</script>

<style lang="scss">
.draft-midia {
  width: 100%;
  display: flex;
  .inner {
    position: relative;
    padding: 0;
    display: flex;
    width: 100%;
    height: 100%;
    gap: 0;
    overflow: hidden;
    flex-direction: column;
    align-items: center;
    background-color: #fafafa;
    border: 1px solid #ccc;
    .inner-status {
      position: absolute;
      display: inline-block;
      width: 20px;
      height: 20px;
      top: 1px;
      left: 1px;
      border-radius: 50%;
      font-size: 0;
      z-index: 1;

      &:hover {
        width: auto;
        height: auto;
        border-radius: 0%;
        top: 0px;
        left: 0px;
        padding: 2px 3px;
        color: #fff;
        font-size: 1rem;
        line-height: 1;
      }

      &.border-green, &.border-red, &.border-yellow {
        &::before {
          content: " ";
          z-index: 1;
        }
      }
      &.border-green {
        background-color: #00a65add;
      }
      &.border-red {
        background-color: #f56954dd;
      }
      &.border-yellow {
        background-color: #ffd35add;
        color: black;
      }
    }
    .inner-action {
      background-color: #fff;
      position: fixed;
      color: #444;
      border-radius: 3px;
      opacity: 0;
      z-index: 1;
      .btn {
        opacity: 0.4;
        border-width: 0px;
        color: #444;
        cursor: pointer;
        &:hover {
          opacity: 1;
        }
      }
      .dropdown-item {
        cursor: pointer;
      }
      .dropdown-menu {
        position: fixed;
      }
    }
    .innerimg {
      max-height: 35vh;
      padding: 5px;
      position: relative;
      z-index: 0;
      line-height: 1;
      img {
        border: 1px solid #ccc;
        max-width: 100%;
      }
      .img-actions {
        * {
          line-height: 1;
          height: auto;
        }
        position: absolute;
        bottom: 7px;
        right: 7px;
        opacity: 0;
        display: flex;
        gap: 2px;

        output {
          text-align: center;
        }
        .b-form-spinbutton {
          padding: 2px 1px;
        }
        .btn {
          padding: 2px 4px;
        }
      }
      &:hover {
        .img-actions {
          opacity: 0.8;
        }
      }
    }
    .innerdesc {
      width: 90%;
      text-align: center;
      display: flex;
      flex-direction: column;
    }
    &:hover {
      .inner-action {
        opacity: 1;
      }
    }
  }
  img {
    height: 100%;
  }
}
</style>
