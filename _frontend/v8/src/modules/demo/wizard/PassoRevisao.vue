<template>
  <div>
    <p class="mb-4 text-sm text-texto-suave">
      Confira os dados. Ao concluir, eles são enviados à API da demonstração, que valida e
      responde como se tivesse gravado.
    </p>
    <dl class="v8-lista-dados">
      <dt>Nome</dt>
      <dd>{{ dados.nome }}</dd>
      <dt>E-mail</dt>
      <dd>{{ dados.email }}</dd>
      <dt>Cidade</dt>
      <dd>{{ dados.cidade }}</dd>
      <dt>Situação</dt>
      <dd>
        <EtiquetaSituacao :situacao="dados.situacao" />
      </dd>
      <template v-if="dados.motivo">
        <dt>Motivo</dt>
        <dd>{{ dados.motivo }}</dd>
      </template>
    </dl>
  </div>
</template>
<script setup>
// Último passo do wizard "Novo cliente" (V8-DEMO-023): só leitura do que foi preenchido.

// 1. Imports
import EtiquetaSituacao from '~@/modules/demo/componentes/EtiquetaSituacao.vue'

// 2. Composables
// 3. Props & Emits
defineProps({
  dados: {
    type: Object,
    required: true
  },
  // Faz parte do contrato dos passos, mas este não tem campo a marcar.
  erros: {
    type: Object,
    default: () => ({})
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
