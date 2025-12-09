<template>
  <div
    :id="`pvd-${item.__label__}-${item.id}`"
    :class="['processo-votacao-display', item.__label__ ]"
  >
    <div
      class="display-controls"
      v-if="!userIsAdminSessao"
    >
      <button
        :id="`auto-rolagem-${item.__label__}-${item.id}`"
        type="button"
        :class="['btn-auto-rolagem', isAutoRolagem ? 'active' : '']"
        @click="clickAutoRolagem"
      >
        Autorrolagem?
        <font-awesome-icon icon="fa-solid fa-up-down" />
      </button>
    </div>
    <div class="display-content">
      <template v-if="!votacaoAberta && !votacaoPedidoPrazoAberta">
        <div
          class="status-votacao"
          v-for="registro in registrosVotacao"
          :key="`rv-${registro.id}`"
        >
          <div
            class="votos"
            v-if="statusVotacao(registro) !== 'result-vista'"
          >
            <div
              class="voto-abs"
              v-if="registro.numero_abstencoes"
            >
              <span class="valor">{{ registro.numero_abstencoes }}</span>
              <span class="titulo">ABS</span>
            </div>
            <div class="voto-nao">
              <span class="valor">{{ registro.numero_votos_nao }}</span>
              <span class="titulo">NÃO</span>
            </div>
            <div class="voto-sim">
              <span class="valor">{{ registro.numero_votos_sim }}</span>
              <span class="titulo">SIM</span>
            </div>
          </div>
          <div :class="statusVotacao(registro)">
            <span>{{ syncStore.data_cache?.sessao_tiporesultadovotacao?.[registro.tipo_resultado_votacao]?.nome }}</span>
          </div>
        </div>
      </template>
      <div
        class="status-votacao"
        v-if="votacaoAberta || discussaoAberta || votacaoPedidoPrazoAberta || registrosVotacao.length === 0"
      >
        <div
          :class="statusVotacao(null)"
          v-if="votacaoAberta || discussaoAberta || votacaoPedidoPrazoAberta"
        >
          <span v-if="votacaoPedidoPrazoAberta">VOTAÇÃO ABERTA PARA PEDIDO DE ADIAMENTO</span>
          <span v-else-if="votacaoAberta">VOTAÇÃO ABERTA</span>
          <span v-else-if="discussaoAberta">DISCUSSÃO ABERTA</span>
        </div>
        <div
          :class="statusVotacao(null)"
          v-else
        >
          <span v-if="item.resultado">{{ item.resultado }}</span>
          <span v-else-if="item.tipo_votacao === 4 && item.votacao_aberta">Leitura em Andamento</span>
          <span v-else-if="registrosVotacao.length === 0">Tramitando</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { computed, watch, ref, inject } from 'vue'

const syncStore = useSyncStore()
const authStore = useAuthStore()

const emit = defineEmits(['resync'])
const EventBus = inject('EventBus')

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  sessao: {
    type: Object,
    required: true
  }
})

const isAutoRolagem = ref(true)
const clickAutoRolagem = () => {
  if (userIsAdminSessao.value) {
    return
  }
  isAutoRolagem.value = !isAutoRolagem.value
  EventBus.emit('toggle-auto-rolagem', {
    isState: isAutoRolagem.value
  })
}
EventBus.on('toggle-auto-rolagem', (payload) => {
  isAutoRolagem.value = payload.isState
  runAutoRolagem()
})

EventBus.on('disable-auto-rolagem', () => {
  isAutoRolagem.value = false
})

const userIsAdminSessao = computed(() => {
  return authStore.hasPermission('sessao.add_sessaoplenaria')
})

const runAutoRolagem = () => {
  if (userIsAdminSessao.value) {
    return
  }
  if (!isAutoRolagem.value || !conditionalAutoRolagem.value) {
    return
  }
  // console.debug('Executando auto rolagem para o item de sessão', props.item.__label__, props.item.id)
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
      behavior: 'smooth'
    })
  }, 100)
}

const registrosVotacao = computed(() => {
  const allRegistrosVotacao = syncStore.data_cache?.sessao_registrovotacao || {}
  const registrosForItem = Object.values(
    allRegistrosVotacao
  ).filter(
    rv => rv.ordem === props.item.id
  )
  registrosForItem.sort((a, b) => a.id - b.id)
  return registrosForItem
})

const votacaoAberta = computed(() => {
  return (props.item.votacao_aberta &&
    props.item.tipo_votacao <= 2
  )
})

const discussaoAberta = computed(() => {
  return (props.item.discussao_aberta &&
    props.item.tipo_votacao <= 2
  )
})

const votacaoPedidoPrazoAberta = computed(() => {
  return (props.item.votacao_aberta_pedido_prazo &&
    props.item.tipo_votacao <= 2
  )
})

const conditionalAutoRolagem = computed(() => {
  return props.item.discussao_aberta || props.item.votacao_aberta || props.item.votacao_aberta_pedido_prazo
})

watch(votacaoAberta, (newValue, oldValue) => {
    if (!newValue && oldValue) {
      emit('resync')
    }
    if (newValue) {
      runAutoRolagem()
    }
  },
  { immediate: true }
)

watch(conditionalAutoRolagem, (newValue) => {
    if (newValue) {
      runAutoRolagem()
    }
  },
  { immediate: true }
)

const statusVotacao = (registro) => {
  let tipo = 'tramitando'

  let r = null
  if (registro) {
    r = syncStore.data_cache?.sessao_tiporesultadovotacao?.[registro.tipo_resultado_votacao]?.nome
  } else if (props.item.resultado) {
    r = props.item.resultado
  }
  if (discussaoAberta.value) {
    tipo = 'result discussao-aberta'
  } else if (votacaoAberta.value) {
    tipo = 'result votacao-aberta'
  } else if (r === 'Aprovado') {
    tipo = 'result result-aprovado'
  } else if (r === 'Rejeitado') {
    tipo = 'result result-rejeitado'
  } else if (r === 'Pedido de Vista') {
    tipo = 'result result-vista'
  } else if (r === 'Prazo Regimental') {
    tipo = 'result result-prazo'
  } else if (r === 'Matéria Lida') {
    tipo = 'result result-lida'
  }

  return tipo
}

</script>

<style lang="scss">
.processo-votacao-display {
  position: absolute;
  right: 0em;
  top: 0em;
  display: flex;
  align-items: flex-start;

  .display-content {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 1px;
    line-height: 1;
  }

  .status-votacao {
    display: flex;
    flex-direction: row;
    justify-content: stretch;
    gap: 1px;

    right: 0;
    color: #fff;
    line-height: 1;
    z-index: 1;

    font-size: 0.7em;
    font-weight: bold;

    & > div  {
      display: flex;
      padding: 3px 10px 4px;
      align-items: stretch;
      white-space: nowrap;
      justify-content: center;
      gap: 1px;
    }
    .tramitando {
      background-color: #e6bc02;
    }
    .votos {
      padding: 0;
      opacity: 0.6;
      div {
        padding: 2px 10px 1px;
        display: flex;
        gap: 2px;
        .titulo {
          font-size: 60%;
        }
        .valor {
          font-size: 130%;
          padding-right: 5px;
        }
      }
      .voto-sim {
        background-color: #008000;
        .titulo, .valor {
        }
      }
      .voto-nao {
        background-color: #ff0000;
        .titulo, .valor {
        }
      }
      .voto-abs {
        background-color: #e6bc02;
        .titulo, .valor {
        }
      }
    }
    .result {
      flex: 2 1 100%;
      min-width: 10em;
      opacity: 0.6;
    }
    .result-aprovado {
      background-color: green;
    }
    .result-prazo {
      background-color: #2580f7;
    }
    .result-vista {
      background-color: #2580f7;
    }
    .result-rejeitado {
      background-color: red;
    }
    .result-lida {
      background-color: #808080;
      opacity: 1;
    }
    .votacao-aberta {
      background-color: #000;
      opacity: 1;
    }
    .discussao-aberta {
      background-color: #3cff00;
      color: #000;
      font-size: 1.2em;
      opacity: 1;
    }
  }

  &:hover {
    .result {
      opacity: 1;
    }
    .votos {
      opacity: 1;
    }
  }

  .display-controls {
    display: flex;
    gap: 0.5em;

    .btn-auto-rolagem {
      color: var(--bs-gray-500);
      background-color: transparent;
      border: none;
      padding: 0.3em 0.5em;
      font-size: 0.8em;
      white-space: nowrap;
      cursor: pointer;
      &.active {
        color: var(--bs-success);
      }
      &:hover {
      }
    }
  }

}

@media screen and (min-width: 768px) {
  .processo-votacao-display {
    .status-votacao {
      font-size: 1em;
      & > div  {
        padding: 3px 10px 2px;
      }
    }
  }
}
</style>
