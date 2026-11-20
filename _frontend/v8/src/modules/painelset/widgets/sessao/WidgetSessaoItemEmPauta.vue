<template>
  <div
    class="widget-sessao-item-em-pauta"
  >
    <div class="inner">
      <div class="inner-materia">
        <div class="parte_sessao">
          <div class="titulo_parte" v-html="parteSessao"></div>
        </div>
        <div class="epigrafe">
          {{ ultimaMateriaMostrada?.__str__ || '' }}
        </div>
        <div class="ementa">
          {{ ultimaMateriaMostrada?.ementa || '' }}
        </div>
      </div>
      <div class="inner-resultado">
        <div class="inner-tramitacao">
          <div class="inner-discussao" v-if="ultimoItemSessaoMostrado?.discussao_aberta">
            EM DISCUSSÃO
          </div>
          <div class="inner-votacao" v-else-if="ultimoItemSessaoMostrado?.votacao_aberta_pedido_prazo">
            EM VOTAÇÃO PEDIDO DE ADIAMENTO
          </div>
          <div class="inner-votacao" v-else-if="ultimoItemSessaoMostrado?.votacao_aberta && ultimoItemSessaoMostrado?.tipo_votacao < 4 && !ultimoItemSessaoMostrado?.votacao_aberta_pedido_prazo">
            EM VOTAÇÃO {{ tipo_votacao[ultimoItemSessaoMostrado?.tipo_votacao] || '' }}
          </div>
          <div class="inner-votacao" v-else-if="ultimoItemSessaoMostrado?.votacao_aberta && ultimoItemSessaoMostrado?.tipo_votacao === 4">
            LEITURA DA MATÉRIA
          </div>
        </div>
        <div class="inner-votacao" v-if="registroLeitura && ultimoItemSessaoMostrado?.tipo_votacao === 4">
          MATÉRIA LIDA EM PLENÁRIO
        </div>
        <div
          :class="['inner-votacao', tipoResultadoVotacao?.natureza || '']"
          v-else-if="registroVotacao"
        >
          <div class="label" v-if="tipoResultadoVotacao.nome !== 'Pedido de Vista'">
            VOTAÇÃO {{ tipo_votacao[ultimoItemSessaoMostrado?.tipo_votacao]}} - <span v-html="tipoResultadoVotacao.nome"></span>
          </div>
          <div class="label" v-else>MATÉRIA COM PEDIDO DE VISTA</div>
          <div :class="['results', tipoResultadoVotacao?.natureza || '']" v-if="tipoResultadoVotacao.nome !== 'Pedido de Vista'">
            <div class="result sim">
              SIM: {{ registroVotacao?.numero_votos_sim || 0 }}
            </div>
            <div class="result nao">
              NÃO: {{ registroVotacao?.numero_votos_nao || 0 }}
            </div>
            <div class="result abstencao" v-if="registroVotacao?.numero_abstencoes">
              ABSTENÇÃO: {{ registroVotacao?.numero_abstencoes || 0 }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed, watch, ref } from 'vue'

const syncStore = useSyncStore()

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  widgetSelected: {
    type: Number,
    default: 0
  }
})

const tipo_votacao = {
  1: 'SIMBÓLICA',
  2: 'NOMINAL',
  3: 'SECRETA',
  4: 'LEITURA'
}

const ultimaMateriaMostrada = ref(null)
const ultimoItemSessaoMostrado = ref(null)
const parteSessao = ref('')

const widgetContainer = computed(() => {
  return syncStore.data_cache.painelset_widget?.[props.widgetSelected] || null
})

const painel = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelId] || null
})

const sessaoPlenaria = computed(() => {
  return syncStore.data_cache.sessao_sessaoplenaria
    ?.[painel.value?.sessao] || null
})

const expedienteMateriaVotacaoAberta = computed(() => {
  const expedientes =
    syncStore.data_cache.sessao_expedientemateria || {}

  return Object.values(expedientes).find(
    (expediente) =>
      expediente.sessao_plenaria === sessaoPlenaria.value?.id &&
      (expediente.discussao_aberta === true ||
      expediente.votacao_aberta === true ||
      expediente.votacao_pedido_prazo === true)
  ) || null
})

const ordemDiaMateriaVotacaoAberta = computed(() => {
  const ordensDia =
    syncStore.data_cache.sessao_ordemdia || {}

  return Object.values(ordensDia).find(
    (ordemDia) =>
      ordemDia.sessao_plenaria === sessaoPlenaria.value?.id &&
      (ordemDia.discussao_aberta === true ||
      ordemDia.votacao_aberta === true ||
      ordemDia.votacao_pedido_prazo === true)
  ) || null
})

const itemSessao = computed(() => {
  if (expedienteMateriaVotacaoAberta.value) {
    return expedienteMateriaVotacaoAberta.value
  }
  if (ordemDiaMateriaVotacaoAberta.value) {
    return ordemDiaMateriaVotacaoAberta.value
  }
  return null
})

const materia = computed(() => {
  if (expedienteMateriaVotacaoAberta.value) {
    return syncStore.data_cache.materia_materialegislativa?.[
      expedienteMateriaVotacaoAberta.value.materia.id ||
      expedienteMateriaVotacaoAberta.value.materia
    ] || null
  }
  if (ordemDiaMateriaVotacaoAberta.value) {
    return syncStore.data_cache.materia_materialegislativa?.[
      ordemDiaMateriaVotacaoAberta.value.materia.id ||
      ordemDiaMateriaVotacaoAberta.value.materia
    ] || null
  }
  return null
})

const registroVotacao = computed(() => {
  const registros = syncStore.data_cache.sessao_registrovotacao || {}

  // recupera o objeto registro de votação correspondente ao último item de sessão mostrado e à última matéria mostrada
  // em caso de mais um registro encontrado, retornar o ultimo (mais recente), com base no id do registro
  const ultimoRegistro = Object.values(registros).reduce((acc, registro) => {
    if (
      (registro.expediente === ultimoItemSessaoMostrado.value?.id ||
      registro.ordem === ultimoItemSessaoMostrado.value?.id) &&
      !ultimoItemSessaoMostrado.value.votacao_aberta &&
      (registro.materia === ultimaMateriaMostrada.value?.id ||
      registro.materia.id === ultimaMateriaMostrada.value?.id)
    ) {
      if (!acc || registro.id > acc.id) {
        return registro
      }
    }
    return acc
  }, null)
  return ultimoRegistro
})

const registroLeitura = computed(() => {
  const registros = syncStore.data_cache.sessao_registroleitura || {}

  return Object.values(registros).find(
    (registro) =>
      (registro.expediente === ultimoItemSessaoMostrado.value?.id ||
      registro.ordem === ultimoItemSessaoMostrado.value?.id) &&
      (registro.materia === ultimaMateriaMostrada.value?.id ||
      registro.materia.id === ultimaMateriaMostrada.value?.id)
  ) || null
})

const tipoResultadoVotacao = computed(() => {
  return syncStore.data_cache.sessao_tiporesultadovotacao[registroVotacao.value?.tipo_resultado_votacao] || {}
})

watch(
  () => expedienteMateriaVotacaoAberta.value,
  (newVal) => {
    if (newVal) {
      syncStore.fetchSync({
        app: 'sessao',
        model: 'registrovotacao',
        params: {
          expediente: newVal.id,
          page_size: 100
        },
        force_fetch: false // se registrovotacao já está no registro de models, os registros de votação já estão sendo monitorados pelo SyncStore
      })
    }
  },
  { immediate: true }
)
watch(
  () => materia.value,
  (newVal) => {
    if (newVal) {
      ultimaMateriaMostrada.value = newVal
      if (expedienteMateriaVotacaoAberta.value) {
        parteSessao.value = 'EXPEDIENTE'
      } else if (ordemDiaMateriaVotacaoAberta.value) {
        parteSessao.value = 'ORDEM DO DIA'
      }
    }
  },
  { immediate: true }
)

watch(
  () => itemSessao.value,
  (newVal) => {
    if (newVal) {
      ultimoItemSessaoMostrado.value = newVal
      let params = {page_size: 100}
      if (newVal.__label__ === 'sessao_expedientemateria') {
        params.expediente = newVal.id
      } else if (newVal.__label__ === 'sessao_ordemdia') {
        params.ordem = newVal.id
      }
      syncStore.fetchSync({
        params,
        app: 'sessao',
        model: 'registrovotacao',
        force_fetch: false // se registrovotacao já está no registro de models, os registros de votação já estão sendo monitorados pelo SyncStore
      })
      syncStore.fetchSync({
        params,
        app: 'sessao',
        model: 'registroleitura',
        force_fetch: false // se registroleitura já está no registro de models, os registros de leitura já estão sendo monitorados pelo SyncStore
      })
      syncStore.fetchSync({
        params,
        app: 'sessao',
        model: 'votoparlamentar',
        force_fetch: false // se votoparlamentar já está no registro de models, os votos parlamentares já estão sendo monitorados pelo SyncStore
      })
    } else {
      if (ultimoItemSessaoMostrado.value) {
        ultimoItemSessaoMostrado.value.votacao_aberta = false
        ultimoItemSessaoMostrado.value.votacao_aberta_pedido_prazo = false
        ultimoItemSessaoMostrado.value.discussao_aberta = false
      }
    }
  },
  { immediate: true }
)

const strFotografiaUrl = (id) => {
  return `/api/parlamentares/parlamentar/${id}/fotografia.c128.png`
}

const syncInit = async () => {
  syncStore.fetchSync({
    app: 'sessao',
    model: 'expedientemateria',
    params: {
      sessao_plenaria: sessaoPlenaria.value?.id || 0,
      page_size: 100,
      expand: 'materia',
      exclude: 'materia.metadata'
    }
  })
  syncStore.fetchSync({
    app: 'sessao',
    model: 'ordemdia',
    params: {
      sessao_plenaria: sessaoPlenaria.value?.id || 0,
      page_size: 100,
      expand: 'materia',
      exclude: 'materia.metadata'
    }
  })
  syncStore.fetchSync({
    app: 'sessao',
    model: 'tiporesultadovotacao',
    params: { page_size: 100 }
  })
}

syncInit()

</script>
<style lang="scss" scoped>
  .widget-sessao-item-em-pauta {
    flex: 0 0 100%;
    .inner {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 100%;
    }
    .parte_sessao {
      background-color: #444a;
      padding: 0.3em 0.5em;
      .titulo_parte {
        font-size: 2em;
        font-weight: bold;
        color: rgb(255, 166, 0);
        text-align: right;
        // letras em maiúsculas
        text-transform: uppercase;
      }
    }
    .inner-materia {
      //border-radius: 1em;
      overflow: hidden;
      .epigrafe {
        font-size: 2em;
        font-weight: bold;
        padding: 1em;
        background-color: #0008;
        color: #ff0;
        // letras em maiúsculas
        text-transform: uppercase;
      }
      .ementa {
        padding: 0 1em;
        font-size: 2.5em;
        line-height: 1.4;
      }
    }
    .inner-discussao, .inner-votacao {
      background-color: #4444;
      padding: 0.3em 0.5em;
      font-size: 2.5em;
      font-weight: bold;
      color: #ff0;
      text-align: center;
      // letras em maiúsculas
      text-transform: uppercase;
    }
    .results {
      display: flex;
      justify-content: space-around;
      margin-top: 0.5em;
      font-size: 1.5em;
      .result {
        &.sim {
          color: #00ff00;
        }
        &.nao {
          color: #ff0000;
        }
        &.abstencao {
          color: #ff9900;
        }
      }
      &.A {
        background-color: #00ff0022;
      }
      &.R {
        background-color: #ff000055;
      }
      &.P {
        background-color: #0000ff55;
      }
    }
    .inner-votacao.A {
      background-color: #4caf5055;
      color: #0f0;
    }
    .inner-votacao.R {
      background-color: #f4433655;
      color: #f00;
      .results {
        .result.nao {
          color: #fff
        }
      }
    }
    .inner-votacao.P {
      background-color: #0000ff55;
      color: #fff;
    }
  }
</style>
