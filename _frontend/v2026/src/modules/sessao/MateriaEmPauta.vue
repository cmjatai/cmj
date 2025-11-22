<template>
  <div
    :id="`mp-${item.__label__}-${item.id}`"
    class="materia-em-pauta"
  >
    <div class="inner-materia">
      <div class="epigrafe">
        <a
          :href="materia.link_detail_backend"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ materia.__str__ }}
        </a>
      </div>
      <div class="protocolo-data-autoria">
        <div class="protocolo-data">
          <div class="protocolo">
            Protocolo:
            <strong>{{ materia.numero_protocolo }}</strong>
          </div>
          <div class="data">
            {{ data_apresentacao }}
          </div>
        </div>
        <div class="autoria">
          <span
            v-for="(autor, key) in autores"
            :key="`au${key}`"
          >{{ autor.nome }}</span>
        </div>
      </div>
      <div class="link-file">
        <a
          v-if="materia.texto_original"
          :href="materia.texto_original"
          target="_blank"
          rel="noopener noreferrer"
        >
          <FontAwesomeIcon icon="file-lines" />
        </a>
      </div>
      <div
        class="ementa"
        v-html="materia.ementa"
      />
      <div class="tramitacao">
        <div class="status">
          <strong>Situação:</strong>&nbsp;
          <span>
            {{ tramitacao.status }}
          </span>
        </div>
        <div class="ultima-acao">
          <strong>Última Ação:</strong>&nbsp;
          {{ tramitacao.texto }}
        </div>
      </div>

      <div
        v-if="item && item.observacao"
        @click="toggleRitoOpened()"
        :class="['rito-text', ritoOpened ? 'open' : 'closed']"
        v-html="ritoOpened ? observacaoHtml : 'Visualizar o Roteiro...'"
      />

      <div
        class="documentos-acessorios pt-2"
        v-if="documentosAcessorios.length > 0"
      >
        <div class="title">
          <strong>Documentos Acessórios</strong>
        </div>
        <ul class="inner-docacess">
          <li
            v-for="doc in documentosAcessorios"
            :key="`docacessorio-${doc.id}`"
            class="doc-acessorio-item"
          >
            <a
              :href="doc.arquivo"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ doc.__str__ }}
            </a>
          </li>
        </ul>
      </div>
      <div
        class="legislacao-citada pt-2"
        v-if="legislacaoCitada.length > 0"
      >
        <div class="title">
          <strong>Legislação Citada</strong>
        </div>
        <ul class="inner-legcitada">
          <li
            v-for="leg in legislacaoCitada"
            :key="`legcitada-${leg.id}`"
            class="leg-citada-item"
          >
            <a
              href="#"
              @click.prevent="modalLegisCitada = leg"
              :key="`legiscit${leg.id}`"
            >
              {{ leg.__str__ }}
            </a>
          </li>
        </ul>
      </div>
    </div>
    <Teleport
      v-if="modalLegisCitada"
      :to="`#modalCmj`"
    >
      <NormaSimpleModalView
        :html-id="`modal-legis-citada-${modalLegisCitada.id}`"
        :norma-id="modalLegisCitada.norma"
        @close="modalLegisCitada = null"
      />
    </Teleport>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import NormaSimpleModalView from '~@/components/NormaSimpleModalView.vue'
import { ref, inject, computed, watch } from 'vue'

const syncStore = useSyncStore()
const EventBus = inject('EventBus')

const emit = defineEmits(['resync'])

const props = defineProps({
  materiaId: {
    type: Number,
    required: true
  },
  item: {
    type: Object,
    required: false,
    default: null
  },
  sessao: {
    type: Object,
    required: true
  }
})

const modalLegisCitada = ref(null)
const ritoOpened = ref(false)

EventBus.on('rito-toggle', () => {
  ritoOpened.value = !ritoOpened.value
})
const toggleRitoOpened = () => {
  EventBus.emit('rito-toggle')
  setTimeout(() => {
    const preview = document.getElementById(`is-${props.item.__label__}-${props.item.id}`)
    let curtop = 0
    let obj = preview
    do {
      curtop += obj.offsetTop
      obj = obj.offsetParent
    } while (obj && obj.tagName !== 'BODY')
    window.scrollTo({
      top: curtop - 100,
      behavior: 'instant'
    })
  }, 100)
}

const observacaoHtml = computed(() => {
  return (props.item.observacao || '').replace(/\n/g, '<br/>')
})

const materia = computed(() => {
  return syncStore.data_cache?.materia_materialegislativa?.[props.materiaId] || { __str__: 'Buscando Matéria Legislativa...' }
})

const tramitacao = computed(() => {
  const tramitacao = syncStore.data_cache?.materia_tramitacao?.[
    props.sessao.finalizada ?
      materia.value.ultima_tramitacao
        : (props.item.tramitacao || materia.value.ultima_tramitacao)
  ] || null
  const status = tramitacao ? syncStore.data_cache?.materia_statustramitacao?.[tramitacao.status] || null : null
  return {
    ...tramitacao,
    status: status ? status.__str__ : 'Status não disponível'
  }
})

const autores = computed(() => {
  const allAutores = syncStore.data_cache?.base_autor || {}
  if (!materia.value.autores || materia.value.autores.length === 0) {
    return []
  }
  return materia.value.autores.map(
    autorId => allAutores[autorId]
  ).filter(autor => autor !== undefined)
})

const data_apresentacao = computed(() => {
  if (!materia.value.data_apresentacao) {
    return ''
  }
  const dateObj = new Date(materia.value.data_apresentacao)
  return dateObj.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
})

const documentosAcessorios = computed(() => {
  const allDocumentos = syncStore.data_cache?.materia_documentoacessorio || {}
  return Object.values(allDocumentos).filter(
    doc => doc.materia === props.item.materia
  )
})

const legislacaoCitada = computed(() => {
  const allLegislacoes = syncStore.data_cache?.norma_legislacaocitada || {}
  return Object.values(allLegislacoes).filter(
    leg => leg.materia === props.item.materia
  )
})

watch(
  () => tramitacao.value,
  (newVal) => {
    if (!newVal?.id) {
      if (props.sessao.finalizada) {
        syncStore.fetchSync({
          app: 'materia',
          model: 'materialegislativa',
          id: materia.value.id
        })
      } else {
        if (props.item.tramitacao) {
          syncStore.fetchSync({
            app: 'materia',
            model: 'tramitacao',
            id: props.item.tramitacao
          })
        }
      }
    }
  },
  { immediate: true }
)

watch(modalLegisCitada, (newVal) => {
  if (newVal === null) {
    return
  }
  // Carrega a norma citada, se necessário
  syncStore.fetchSync({
    app: 'norma',
    model: 'normajuridica',
    id: newVal.norma,
    params: {
      exclude: 'metadata'
    }
  })
  // $(`#modal-legis-citada-${newVal.id}`).modal('show')
  //$(`#modal-legis-citada-${newVal.id}`).on('hidden.bs.modal', function (e) {
  //  modalLegisCitada.value = null
  //})
})

watch( materia, (newVal) => {
  if (!newVal?.id) {
    emit('resync')
  }
}, { immediate: true } )

</script>
<style lang="scss">
.materia-em-pauta {
  .inner-materia {
    .epigrafe {
      display: flex;
      flex-direction: column;
      font-weight: bold;
      text-decoration: none;
      font-size: 0.8em;
      align-items: flex-start;
      a {
        display: inline-block
      }
    }
    .protocolo-data-autoria {
      display: flex;
      flex-direction: column;
      line-height: 1.15;
      padding: 0.2em 0 0 0.5em;

      .protocolo-data {
        display: flex;
        font-size: 0.9em;
        align-items: center;
        color: var(--bs-secondary);
        gap: 0.5em;
        .data {
          border-left: 1px solid #777;
          padding-left: 0.5em;
        }
      }
      .protocolo {
        color: var(--bs-code-color);
        white-space: nowrap;
      }
      .autoria {
        margin-left: 0.5em;
        padding: 0.2em 0 0 0.5em;
        font-size: 0.9em;
        border-left: 1px solid #777;
        font-weight: bold;
        span:not(:last-child)::after {
          content: "; ";
          flex: auto;
        }
      }
    }
    .link-file {
      float: left;
      font-size: 1.5em;
      margin-left: -0.3em;
      a {
        padding: 0.5em;
        display: inline-block;
        color: var(--bs-link-color);
        &:hover {
          background-color: var(--bs-link-hover-color);
          color: white;
          border-radius: 5px;
        }
      }
    }
    .ementa {
      margin-top: 0.2em;
      font-size: 1.2em;
      line-height: 1.3;
      color: #299680;
    }

    .tramitacao {
      line-height: 1.2;
      margin-top: 0.6em;
      position: relative;
      padding: 0.5em 0 0 0;
      color: var(--bs-secondary);
      &::before {
        content: " ";
        position: absolute;
        top: 0;
        border-top: 1px solid var(--bs-border-color-translucent);
        width: 10em;
        height: 1px;
      }
    }
    .rito-text {
      position: relative;
      display: inline-block;
      margin: 0.5em 0;
      padding: 0.5em;
      background-color: var(--bs-body-bg);
      color: var(--bs-secondary);
      border: 1px solid var(--bs-border-color);
      font-family: var(--bs-font-monospace);
      // white-space: pre-wrap;
      font-size: 0.9em;
      p {
        margin: 0;
        padding: 0;
      }
      &.closed {
        font-size: 80%;
        padding: 0.5em 1em 0.5em 0.5em;
        overflow: hidden;
        cursor: pointer;
        opacity: 0.8;
        &::after {
          content: " ▼";
          position: absolute;
          bottom: 0.8em;
          right: 0.5em;
          font-size: 0.8em;
          color: var(--bs-secondary);
        }
      }
    }
    .legislacao-citada, .documentos-acessorios {
      .title {
        color: var(--bs-primary);
      }
      ul {
        list-style-type: disc;
        margin: 0;
        font-size: 0.9em;
      }
    }
    .doc-acessorio-item, .leg-citada-item {
      padding: 0.5em 0;
    }
  }
}
[data-bs-theme="dark"] {
  .materia-em-pauta {
    .inner-materia {
      .epigrafe {
        color: #4bd2aa;
      }
    }
  }
}

@media screen and (min-width: 768px) {
  .materia-em-pauta {
    .inner-materia {
      .epigrafe {
        font-size: 1.2em;
      }
      .protocolo-data-autoria {
        flex-direction: row;
        align-items: center;
      }
      .ementa {
        font-size: 1.5em;
        padding: 0.3em 0;
      }
    }
  }
}
</style>
