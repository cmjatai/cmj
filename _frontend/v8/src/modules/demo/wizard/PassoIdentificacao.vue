<template>
  <div>
    <!-- eslint-disable vue/no-mutating-props -->
    <CampoForm
      v-slot="campo"
      rotulo="Nome"
      :erro="erros.nome?.[0] || ''"
    >
      <input
        :id="campo.id"
        v-model="dados.nome"
        class="v8-entrada"
        type="text"
        maxlength="80"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="E-mail"
      :erro="erros.email?.[0] || ''"
    >
      <input
        :id="campo.id"
        v-model="dados.email"
        class="v8-entrada"
        type="email"
        maxlength="120"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
  </div>
</template>
<script setup>
// Primeiro passo do wizard "Novo cliente" (V8-DEMO-023): nome e e-mail.
// `dados` é o objeto reativo comum a todos os passos, e o passo o altera direto: é o contrato do
// ModalWizard, e por isso a regra vue/no-mutating-props está desligada no template.

// 1. Imports
import CampoForm from '~@/overlays/CampoForm.vue'

// 2. Composables
// 3. Props & Emits
defineProps({
  dados: {
    type: Object,
    required: true
  },
  // { campo: [mensagens] }, vindo do `validar` do passo.
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
