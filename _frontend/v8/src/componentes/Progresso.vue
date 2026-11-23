<template>
  <ProgressRoot
    v-model="valor"
    class="v8-progresso"
    :max="max"
    :get-value-label="rotuloDoValor"
  >
    <ProgressIndicator
      class="v8-progresso-indicador"
      :style="{ transform: `translateX(-${100 - porcentagem}%)` }"
    />
  </ProgressRoot>
</template>

<script setup>
// Barra de progresso (docs/specs/v8/componentes.md), sobre o Progress do Reka UI. Sem valor
// (`null`), a barra fica indeterminada.
//
//   <Progresso v-model="enviados" :max="total" rotulo="Envio dos arquivos" />

// 1. Imports
import { computed } from 'vue'
import { ProgressIndicator, ProgressRoot } from 'reka-ui'

// 3. Props & Emits
const props = defineProps({
  max: {
    type: Number,
    default: 100
  },
  rotulo: {
    type: String,
    default: ''
  }
})
const valor = defineModel({ type: Number, default: null })

// 5. Computed Properties
const porcentagem = computed(() =>
  valor.value === null || valor.value === undefined ? 0 : Math.round((valor.value / props.max) * 100)
)

// 8. Functions
function rotuloDoValor(atual, maximo) {
  const texto = `${Math.round((atual / maximo) * 100)}%`
  return props.rotulo ? `${props.rotulo}: ${texto}` : texto
}
</script>
