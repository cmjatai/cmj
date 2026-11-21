<template>
  <dl class="v8-lista-dados">
    <dt>E-mail</dt>
    <dd>{{ cliente.email }}</dd>
    <dt>Cidade</dt>
    <dd>{{ cliente.cidade }}</dd>
    <dt>Situação</dt>
    <dd>
      <EtiquetaSituacao :situacao="cliente.situacao" />
    </dd>
    <template v-if="cliente.motivo">
      <dt>Motivo</dt>
      <dd>{{ cliente.motivo }}</dd>
    </template>
    <dt>Cliente desde</dt>
    <dd>
      <time :datetime="cliente.desde">{{ formatarData(cliente.desde) }}</time>
    </dd>
  </dl>
</template>
<script setup>
// Dados cadastrais de um cliente da demo, na mesma ordem da página de detalhe do Django.

// 1. Imports
import EtiquetaSituacao from '~@/modules/demo/componentes/EtiquetaSituacao.vue'
import { formatarData } from '~@/modules/demo/formatos'

// 2. Composables
// 3. Props & Emits
defineProps({
  cliente: {
    type: Object,
    required: true
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
