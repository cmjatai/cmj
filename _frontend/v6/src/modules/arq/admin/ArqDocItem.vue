<template>
  <div
    class="arq-doc-item"
    @mousemove="mouseMove"
  >
    <div class="inner">
      <div class="titulo">
        <FontAwesomeIcon
          v-if="arqdoc.checkcheck"
          icon="lock"
          size="xs"
          class="text-light-blue"
          title="ArqClasse Arquivada."
        />&nbsp;
        <a
          :href="arqdoc.link_detail_backend"
          target="_blank"
        >{{ arqdoc.titulo }}</a>
      </div>
      <div
        class="descricao"
        v-html="arqdoc.descricao"
      />
      <div class="rodape">
        <span class="data">Data do Documento: {{ dataComputed }}</span>
        <span class="created">Inclusão no ArqDoc: {{ createdComputed }}</span>
      </div>
      <div class="rodape">
        <BreadCrumbClasse
          v-if="contraClasse"
          :parents="contraClasse.parents"
          :me="contraClasse"
        />
      </div>
      <div
        class="inner-preview"
        ref="previewRef"
      >
        <img
          v-if="imgdisplay"
          ref="imgpreviewRef"
          @error="errorPreview"
          @load="loadPreview"
        >
        <div
          class="actions"
          ref="previewActionsRef"
        >
          <a
            class="previous"
            @click="clickPrevious"
          ><FontAwesomeIcon icon="chevron-left" /></a>
          <a
            class="next"
            @click="clickNext"
          ><FontAwesomeIcon icon="chevron-right" /></a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import Resources from '~@/utils/resources'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import BreadCrumbClasse from './BreadCrumbClasse.vue'

const messageStore = useMessageStore()

const ARQCLASSE_FISICA = 100

const props = defineProps({
  arqdoc: { type: Object, required: true },
  classe: { type: Object, required: true }
})

const imgdisplay = ref(false)
const imgSrc = ref(null)
const dpi = ref(72)
const page = ref(1)
const contraClasse = ref(null)

const previewRef = ref(null)
const imgpreviewRef = ref(null)
const previewActionsRef = ref(null)

const dataComputed = computed(() => props.arqdoc.data.split('-').reverse().join('/'))
const createdComputed = computed(() => new Date(props.arqdoc.created).toLocaleString())

watch(dpi, () => {
  imgSrc.value = `${props.arqdoc.arquivo}?page=${page.value}&dpi=${dpi.value}`
})

watch(page, (nv) => {
  imgSrc.value = `${props.arqdoc.arquivo}?page=${nv}&dpi=${dpi.value}`
})

watch(imgSrc, (nv) => {
  imgdisplay.value = true
  nextTick(() => {
    if (imgpreviewRef.value) {
      imgpreviewRef.value.src = nv
    }
  })
})

function loadPreview () {
  if (previewActionsRef.value) {
    previewActionsRef.value.style.display = 'flex'
  }
}

function errorPreview () {
  if (page.value > 1) {
    page.value -= 1
    messageStore.addMessage({ type: 'info', text: 'Esta é a última página.', timeout: 2000 })
  } else {
    messageStore.addMessage({ type: 'info', text: 'Esta é a primeira página.', timeout: 2000 })
  }
}

function clickPrevious () {
  if (page.value > 1) page.value -= 1
}

function clickNext () {
  page.value += 1
}

function mouseMove (event) {
  if (imgSrc.value === null) {
    imgSrc.value = `${props.arqdoc.arquivo}?page=${page.value}&dpi=${dpi.value}`
  }
  const el = event.currentTarget
  let zoom = (event.offsetX + 30) / el.offsetWidth
  if (zoom > 0.7) zoom = 0.7
  if (!event.target.closest('.inner-preview') && previewRef.value) {
    previewRef.value.style.top = `${zoom * -100 / 1.7}vh`
    previewRef.value.style.bottom = `${zoom * -100 / 1.7}vh`
  }
  if (zoom > 0.5) dpi.value = 300
}

onMounted(() => {
  nextTick(() => {
    const classeId = props.classe.perfil === ARQCLASSE_FISICA
      ? props.arqdoc.classe_logica
      : props.arqdoc.classe_estrutural

    Resources.Utils.fetch({
      app: 'arq',
      model: 'arqclasse',
      id: classeId
    })
      .then((response) => {
        contraClasse.value = response.data
      })
      .catch(() => {
        messageStore.addMessage({ type: 'danger', text: 'Não foi possível recuperar classe selecionada...', timeout: 5000 })
      })
  })
})
</script>

<style lang="scss">
.arq-doc-item {
  padding: 15px 15px 15px 8px;
  border-bottom: 1px solid #eee;
  margin-left: 7px;
  z-index: 0;
  .inner {
    position: relative;
    .descricao {
      padding: 5px 0;
    }
    .rodape {
      font-size: 80%;
      color: #444;
      display: flex;
      gap: 15px;
    }
    .inner-preview {
      background-color: #777;
      position: absolute;
      display: none;
      top: -15px;
      right: -15px;
      bottom: -15px;
      padding: 10px;
      z-index: 1;
      img {
        position: relative;
        height: 100%;
        width: auto;
      }
      .actions {
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        position: absolute;
        display: none;
        align-items: stretch;
        justify-content: end;
        .previous, .next {
          display: flex;
          flex: 0 0 50%;
          justify-content: left;
          align-items: center;
          text-decoration: none;
          cursor: pointer;
          color: #0003;
          padding: 10px 20px;
          font-size: 150%;
          &:hover {
            color: #09f;
          }
        }
        .next {
          justify-content: right;
        }
      }
    }
  }
  &:hover {
    background-color: #f5f5f5;
    padding: 15px 15px 15px 15px;
    margin-left: 0px;
    .inner-preview {
      display: block;
    }
  }
}
</style>
