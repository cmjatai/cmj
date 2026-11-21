<template>
  <OverlayFrame
    v-for="quadro in quadros"
    :key="quadro.id"
    :entrada-id="quadro.id"
    :kind="quadro.kind"
    :type="quadro.type"
    :opcoes="quadro.opcoes"
    :aberto="!quadro.saindo"
    @saiu="descartar(quadro.id)"
  >
    <ConteudoEntrada
      :conteudo="quadro.conteudo"
      :opcoes="quadro.opcoes"
    />
  </OverlayFrame>
</template>
<script setup>
// Montado uma única vez pelo app. Desenha as entradas abertas pelo store (V8-OVL-010).
//
// Uma entrada fechada sai do store na hora. O quadro dela continua aqui só até a animação de
// saída terminar.

// 1. Imports
import { onBeforeUnmount, ref, watch } from 'vue'
import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import OverlayFrame from '~@/overlays/OverlayFrame.vue'
import ConteudoEntrada from '~@/overlays/ConteudoEntrada.vue'

// 2. Composables
const store = useOverlayStore(pinia)

// 3. Props & Emits
// 4. State & Refs
// Tempo máximo de espera pela animação de saída.
const ESPERA_SAIDA = 600
const quadros = ref([])
const esperas = new Map()

// 5. Computed Properties
// 6. Watchers
watch(() => store.hospedadas.map(e => e.id), sincronizar, { immediate: true })

// 7. Events & Lifecycle Hooks
window.addEventListener('beforeunload', aoSairDaPagina)

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', aoSairDaPagina)
  esperas.forEach(espera => clearTimeout(espera))
  esperas.clear()
})

// 8. Functions
function sincronizar(ids) {
  quadros.value.forEach(quadro => {
    if (!quadro.saindo && !ids.includes(quadro.id)) {
      quadro.saindo = true
      esperas.set(quadro.id, setTimeout(() => descartar(quadro.id), ESPERA_SAIDA))
    }
  })
  ids.forEach(id => {
    if (!quadros.value.some(quadro => quadro.id === id)) {
      const entrada = store.entrada(id)
      quadros.value.push({
        id,
        kind: entrada.kind,
        type: entrada.type,
        opcoes: entrada.opcoes,
        conteudo: store.conteudo(id),
        saindo: false
      })
    }
  })
}

function descartar(id) {
  clearTimeout(esperas.get(id))
  esperas.delete(id)
  quadros.value = quadros.value.filter(quadro => quadro.id !== id)
}

// Com alteração não salva, sair da página dispara o aviso do navegador (V8-OVL-025).
function aoSairDaPagina(evento) {
  if (store.temAlteracoes) {
    evento.preventDefault()
    evento.returnValue = ''
  }
}
</script>
