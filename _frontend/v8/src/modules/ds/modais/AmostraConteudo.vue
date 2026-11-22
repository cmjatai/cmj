<template>
  <div>
    <p>{{ texto }}</p>
    <dl class="v8-lista-dados">
      <dt>Nome</dt>
      <dd>Ana Lima</dd>
      <dt>E-mail</dt>
      <dd>ana.lima@exemplo.invalid</dd>
      <dt>Situação</dt>
      <dd><span class="v8-etiqueta v8-etiqueta-ok">Ativo</span></dd>
    </dl>
  </div>
  <OverlayFooter>
    <button
      type="button"
      class="v8-btn v8-btn-primario"
      @click="overlay.close(true)"
    >
      Fechar
    </button>
  </OverlayFooter>
</template>

<script setup>
// Conteúdo de amostra dos modals simples e de tela cheia da vitrine (V8-DS-009).

// 1. Imports
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useOverlay } from '~@/overlays/useOverlay'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
defineProps({
  texto: {
    type: String,
    default: 'Conteúdo do modal.'
  }
})
</script>
