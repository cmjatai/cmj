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
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
  </div>
</template>

<script setup>
// Primeiro passo do assistente de amostra da vitrine (V8-DS-009).

// 1. Imports
import CampoForm from '~@/overlays/CampoForm.vue'

// 3. Props & Emits
defineProps({
  dados: {
    type: Object,
    required: true
  },
  erros: {
    type: Object,
    default: () => ({})
  }
})
</script>
