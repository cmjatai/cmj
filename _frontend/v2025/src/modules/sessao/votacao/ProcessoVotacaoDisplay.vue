<template>
  <div
    :id="`pvd-${item.__label__}-${item.id}`"
    :class="['processo-votacao-display', item.__label__ ]"
  >
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
</template>
<script setup>
// 1. Importações
import { useSyncStore } from '~@/stores/SyncStore'
import { computed, watch } from 'vue'

const syncStore = useSyncStore()

const emit = defineEmits(['resync'])

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

watch(votacaoAberta, (newValue, oldValue) => {
    if (!newValue && oldValue) {
      emit('resync')
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
  } else if (r === 'Matéria lida') {
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
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;

  .status-votacao {
    display: flex;
    flex-direction: row;
    justify-content: stretch;
    gap: 1px;

    right: 0;
    font-weight: bold;
    color: #fff;
    line-height: 1;
    z-index: 1;

    & > div  {
      display: flex;
      padding: 3px 10px 2px;
      align-items: center;
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

}

@media screen and (min-width: 768px) {
  .resultado-votacao {
  }
}
</style>
