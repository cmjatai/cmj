<template>
  <div
    class="widget-registro-presenca"
  >
    <h3>Registro de Presença da Sessão Plenária: {{ sessaoPlenaria?.__str__ }}</h3>
    <p>Aqui será exibido o widget de registro de presença para a sessão plenária associada ao painel.</p>
    <div>
      <div
        :key="`integrante-${integrante.id}`"
        v-for="integrante in integrantesDaMesa"
        class="integrante-mesa"
      >
        {{ integrante.parlamentar }} ({{ integrante.cargo }})
      </div>
      <div
        :key="`parlamentar-presente-${parlamentar.id}`"
        v-for="parlamentar in parlamentaresAtivosPresentes"
        class="parlamentar-presente"
      >
        {{ parlamentar.__str__ }}
      </div>
      <div
        :key="`parlamentar-ausente-${parlamentar.id}`"
        v-for="parlamentar in parlamentaresAtivosAusentes"
        class="parlamentar-ausente"
      >
        {{ parlamentar.__str__ }}
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
  return parlamentares
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
    p => p.ativo && !idsPresentes.includes(p.id)
  )
  return parlamentares
})

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
  .widget-registro-presenca {
  }
</style>
