<template>
  <div
    class="widget-registro-presenca-e-votacao"
  >
    <div class="inner">
      <div
        :key="`integrante-${integrante.id}`"
        v-for="integrante in integrantesDaMesa"
        class="integrante-mesa"
      >
        <div
          class="foto"
          :style="`background-image: url(${strFotografiaUrl(integrante.id)})`"
        />
        <div class="nome">
          {{ integrante.parlamentar }} <small>({{ integrante.cargo }})</small>
        </div>
        <div
          class="votacao"
          v-if="widgetContainer?.config.displayVotacao"
        >
          <span class="sim">SIM</span>
        </div>
      </div>
      <div
        :key="`parlamentar-presente-${parlamentar.id}`"
        v-for="parlamentar in parlamentaresAtivosPresentes"
        class="parlamentar-presente"
      >
        <div
          class="foto"
          :style="`background-image: url(${strFotografiaUrl(parlamentar.id)})`"
        />
        <div class="nome">
          {{ parlamentar.__str__ }} <small>&nbsp;</small>
        </div>
        <div
          class="votacao"
          v-if="widgetContainer?.config.displayVotacao"
        >
          <span class="sim">SIM</span>
        </div>
      </div>
      <template v-if="widgetContainer?.config.displayAusentes">
        <div
          :key="`parlamentar-ausente-${parlamentar.id}`"
          v-for="parlamentar in parlamentaresAtivosAusentes"
          class="parlamentar-ausente"
        >
          <div
            class="foto"
            :style="`background-image: url(${strFotografiaUrl(parlamentar.id)})`"
          />
          <div class="nome">
            {{ parlamentar.__str__ }}<small>&nbsp;</small>
          </div>
          <div
            class="votacao"
            v-if="widgetContainer?.config.displayVotacao"
          >
            <span class="nao">NÃO</span>
          </div>
        </div>
      </template>
      <div class="quorum">
        <div class="inner-quorum">
          <div class="ausentes-label">
            <template v-if="parlamentaresAtivosAusentes.length > 0">
              {{ parlamentaresAtivosAusentes.length }} Ausentes
            </template>
          </div>
          <div class="quorum-label">
            Quórum
            <span class="quorum-value">{{ quorum }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { computed } from 'vue'

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

const integrantesDaMesa = computed(() => {
  if (!sessaoPlenaria.value) {
    return []
  }
  const integrantes = Object.values(syncStore.data_cache.sessao_integrantemesa || {}).filter(
    im => im.sessao_plenaria === sessaoPlenaria.value.id
  )
  const integrantesPorParlamentar = []

  integrantes.forEach(integrante => {
    const parlamentar = syncStore.data_cache.parlamentares_parlamentar?.[integrante.parlamentar] || null
    const cargo = syncStore.data_cache.parlamentares_cargomesa?.[integrante.cargo] || null
    if (parlamentar && cargo) {
      integrantesPorParlamentar.push({
        id: parlamentar.id,
        parlamentar: parlamentar.__str__,
        cargo: cargo.__str__
      })
    }
  })
  return integrantesPorParlamentar
})

// computed para parlamentares ativos e presentes na sessão plenária
const parlamentaresAtivosPresentes = computed(() => {
  if (!sessaoPlenaria.value) {
    return []
  }
  const presencas = Object.values(syncStore.data_cache.sessao_sessaoplenariapresenca || {}).filter(
    sp => sp.sessao_plenaria === sessaoPlenaria.value.id
  )
  const parlamentares = presencas.map(presenca => {
    return syncStore.data_cache.parlamentares_parlamentar?.[presenca.parlamentar] || null
  }).filter(p => p !== null && integrantesDaMesa.value.every(im => im.id !== p.id)) // filtra para não incluir integrantes da mesa
  return _.orderBy(parlamentares, ['nome_parlamentar'], ['asc'])
})
// computed para parlamentares ativos e ausentes na sessão plenária
const parlamentaresAtivosAusentes = computed(() => {
  if (!sessaoPlenaria.value) {
    return []
  }
  // o parlamentar está ausente se ele é ativo e não está na lista de presentes
  const presencas = Object.values(syncStore.data_cache.sessao_sessaoplenariapresenca || {}).filter(
    sp => sp.sessao_plenaria === sessaoPlenaria.value.id
  )
  const idsPresentes = presencas.map(presenca => presenca.parlamentar)
  const parlamentares = Object.values(syncStore.data_cache.parlamentares_parlamentar || {}).filter(
    p => p.ativo && !idsPresentes.includes(p.id) && integrantesDaMesa.value.every(im => im.id !== p.id)
  )
  return _.orderBy(parlamentares, ['nome_parlamentar'], ['asc'])
})

const quorum = computed(() => {
  return integrantesDaMesa.value.length + parlamentaresAtivosPresentes.value.length
})

const strFotografiaUrl = (id) => {
  return `/api/parlamentares/parlamentar/${id}/fotografia.c128.png`
}

const syncInit = async () => {
  syncStore.fetchSync({
    app: 'parlamentares',
    model: 'parlamentar',
    params: {
      ativo: 'True'
    }
  })
    .then(() => {
      // Após carregar os parlamentares, carregar os cargos da mesa
      return syncStore.fetchSync({
        app: 'parlamentares',
        model: 'cargomesa',
        params: {}
      })
        .then(() => {
          // Após carregar os cargos da mesa, carregar os integrantes da mesa
          return syncStore.fetchSync({
            app: 'sessao',
            model: 'integrantemesa',
            params: {
              sessao_plenaria: sessaoPlenaria.value?.id
            }
          })
        })
    })

  syncStore.fetchSync({
    app: 'sessao',
    model: 'sessaoplenariapresenca',
    params: {
      sessao_plenaria: sessaoPlenaria.value?.id
    }
  })

  syncStore.fetchSync({
    app: 'sessao',
    model: 'presencaordemdia',
    params: {
      sessao_plenaria: sessaoPlenaria.value?.id
    }
  })
}

syncInit()

</script>
<style lang="scss" scoped>
  .widget-registro-presenca-e-votacao {
    width: 100%;
    height: 100%;
    .inner {
      display: flex;
      width: 100%;
      height: 100%;
      flex-direction: column;
      justify-content: stretch;
    }
    .integrante-mesa,
    .parlamentar-presente,
    .parlamentar-ausente,
    .quorum {
      flex: 1 1 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5em;
      padding-right: 0.3em;
      .foto {
        height: 100%;
        aspect-ratio: 1 / 1;
        background-size: auto 100%;
      }
      .nome {
        text-align: left;
        flex: 1 1 auto;
        overflow: hidden;
        line-height: 1;
        small {
          font-weight: normal;
          font-size: 0.8em;
          font-style: italic;
          display: block;
          margin-left: 0.2em;
          color: #aaa;
        }
      }
      .votacao {
        font-size: 1em;
        font-weight: bold;
        text-shadow: 1px 1px 3px #000;
        line-height: 1;
        span {
          padding: 0.2em;
          display: inline-block;
          color: #fff;
          border-radius: 0.15em;
          min-width: 4em;
          text-align: center;
          box-shadow: 1px 1px 2px #0006;
        }
        .sim {
          background-color: #0f0;
        }
        .nao {
          background-color: red;
        }
        .abstencao {
          background-color: orange;
        }
        .nao-votou {
          background-color: gray;
        }
      }
    }
    .integrante-mesa {
      &:nth-child(odd) {
        background-color: #00448880;
      }
      &:nth-child(even) {
        background-color: #00448870;
      }
    }
    .parlamentar-presente {
      // odd even background
      &:nth-child(odd) {
        background-color: #00550080;
      }
      &:nth-child(even) {
        background-color: #00550070;
      }
    }
    .parlamentar-ausente {
      // odd even background
      zoom: 0.7;
      color: #aaa;
      &:nth-child(odd) {
        background-color: #55000080;
      }
      &:nth-child(even) {
        background-color: #55000070;
      }
    }
    .quorum {
      flex: 0 0 auto;
      display: flex;
      padding: 0.3em;
      background-color: #222;
      border-top: 2px solid #555;
      .inner-quorum {
        flex: 0 0 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .ausentes-label {
        font-size: 1.1em;
        font-weight: bold;
        color: #f00;
      }
      .quorum-label {
        font-size: 1.4em;
        font-weight: bold;
        color: #0f0;
        background-color: #000;
        border-radius: 0.2em;
        padding: 0.1em 0.5em;
        display: flex;
        align-items: center;
        .quorum-value {
          margin-left: 0.5em;
          font-size: 1.4em;
          color: #fff;
        }
      }
    }

  }
</style>
