<template>
  <div class="v8-campo">
    <label
      class="v8-rotulo"
      :for="id"
    >{{ rotulo }}</label>
    <slot
      :id="id"
      :invalido="invalido ? 'true' : undefined"
      :descrito-por="invalido ? idErro : undefined"
    />
    <p
      v-if="invalido"
      :id="idErro"
      class="v8-erro-campo"
    >
      {{ erro }}
    </p>
  </div>
</template>
<script setup>
// Rótulo, campo e erro de validação. O campo vem pelo slot e recebe id e atributos ARIA:
//
//   <CampoForm rotulo="Nome" :erro="erroDe('nome')" v-slot="campo">
//     <input v-model="valores.nome" class="v8-entrada" :id="campo.id"
//       :aria-invalid="campo.invalido" :aria-describedby="campo.descritoPor">
//   </CampoForm>

// 1. Imports
import { computed, useId } from 'vue'

// 2. Composables
const id = useId()

// 3. Props & Emits
const props = defineProps({
  rotulo: {
    type: String,
    required: true
  },
  erro: {
    type: String,
    default: ''
  }
})

// 4. State & Refs
const idErro = `${id}-erro`

// 5. Computed Properties
const invalido = computed(() => Boolean(props.erro))

// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
