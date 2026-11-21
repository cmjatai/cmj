<template>
  <p class="v8-confirm-mensagem">
    {{ mensagem }}
  </p>
  <OverlayFooter>
    <button
      type="button"
      class="v8-btn"
      data-confirm-botao="cancelar"
      @click="overlay.close(false)"
    >
      {{ rotuloCancelar }}
    </button>
    <button
      type="button"
      :class="['v8-btn', variante === 'perigo' ? 'v8-btn-perigo' : 'v8-btn-primario']"
      data-confirm-botao="ok"
      @click="overlay.close(true)"
    >
      {{ rotuloOk }}
    </button>
  </OverlayFooter>
</template>
<script setup>
// Conteúdo do modal de confirmação (V8-OVL-060). A mensagem entra como texto (V8-OVL-104).

// 1. Imports
import { useOverlay } from '~@/overlays/useOverlay'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
defineOptions({ inheritAttrs: false })
defineProps({
  mensagem: {
    type: String,
    default: 'Confirma esta ação?'
  },
  rotuloOk: {
    type: String,
    default: 'Confirmar'
  },
  rotuloCancelar: {
    type: String,
    default: 'Cancelar'
  },
  variante: {
    type: String,
    default: 'padrao'
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
