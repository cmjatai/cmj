<template>
  <OverlayFrame
    v-if="open"
    kind="drawer"
    :opcoes="opcoes"
    @fechar="emit('update:open', false)"
  >
    <slot />
    <OverlayFooter v-if="$slots.footer">
      <slot name="footer" />
    </OverlayFooter>
  </OverlayFrame>
</template>
<script setup>
// Drawer declarado no template de um componente (V8-OVL-030):
//
//   <Drawer v-model:open="aberto" side="left" mode="docked" mode-estreito="overlay" title="Filtros">
//     ...conteúdo...
//     <template #footer>...ações...</template>
//   </Drawer>

// 1. Imports
import { computed } from 'vue'
import OverlayFrame from '~@/overlays/OverlayFrame.vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  side: {
    type: String,
    default: 'right'
  },
  mode: {
    type: String,
    default: 'overlay'
  },
  // Modo em tela estreita, quando difere do de tela larga (V8-OVL-033).
  modeEstreito: {
    type: String,
    default: null
  },
  size: {
    type: String,
    default: 'md'
  },
  scrim: {
    type: Boolean,
    default: true
  },
  title: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['update:open'])

// 4. State & Refs
// 5. Computed Properties
const opcoes = computed(() => ({
  side: props.side,
  mode: props.mode,
  modeEstreito: props.modeEstreito,
  size: props.size,
  scrim: props.scrim,
  title: props.title
}))

// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
