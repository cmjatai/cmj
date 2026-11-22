<template>
  <div>
    <!-- eslint-disable vue/no-mutating-props -->
    <CampoForm
      v-slot="campo"
      rotulo="Bairro"
      :erro="erros.bairro?.[0] || ''"
    >
      <select
        :id="campo.id"
        v-model="dados.bairro"
        class="v8-entrada"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
        <option value="">
          Escolha
        </option>
        <option
          v-for="bairro in BAIRROS"
          :key="bairro"
          :value="bairro"
        >
          {{ bairro }}
        </option>
      </select>
    </CampoForm>
  </div>
</template>

<script setup>
// Segundo passo do assistente de amostra da vitrine (V8-DS-009).

// 1. Imports
import CampoForm from '~@/overlays/CampoForm.vue'
import { BAIRROS } from '~@/modules/ds/amostras'

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
