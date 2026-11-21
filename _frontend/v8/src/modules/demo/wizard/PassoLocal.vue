<template>
  <div>
    <!-- eslint-disable vue/no-mutating-props -->
    <CampoForm
      v-slot="campo"
      rotulo="Cidade"
      :erro="erros.cidade?.[0] || ''"
    >
      <input
        :id="campo.id"
        v-model="dados.cidade"
        class="v8-entrada"
        type="text"
        maxlength="60"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="Situação"
      :erro="erros.situacao?.[0] || ''"
    >
      <select
        :id="campo.id"
        v-model="dados.situacao"
        class="v8-entrada"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
        <option
          v-for="situacao in SITUACOES"
          :key="situacao.valor"
          :value="situacao.valor"
        >
          {{ situacao.rotulo }}
        </option>
      </select>
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="Motivo da inativação"
      :erro="erros.motivo?.[0] || ''"
    >
      <input
        :id="campo.id"
        v-model="dados.motivo"
        class="v8-entrada"
        type="text"
        maxlength="200"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
  </div>
</template>
<script setup>
// Segundo passo do wizard "Novo cliente" (V8-DEMO-023): cidade, situação e motivo, que é
// exigido do cliente inativo. `dados` é alterado direto, como em PassoIdentificacao.vue.

// 1. Imports
import CampoForm from '~@/overlays/CampoForm.vue'
import { SITUACOES } from '~@/modules/demo/formatos'

// 2. Composables
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

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
