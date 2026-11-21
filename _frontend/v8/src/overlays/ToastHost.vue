<template>
  <Teleport to="body">
    <div
      class="v8-toasts z-(--z-toast)"
      role="region"
      aria-label="Notificações"
    >
      <TransitionGroup name="v8-toast">
        <div
          v-for="toast in toastStore.visiveis"
          :key="toast.id"
          class="v8-toast"
          :class="CLASSES_NIVEL[toast.nivel]"
          :role="toast.nivel === 'error' ? 'alert' : 'status'"
          @mouseenter="segurar(toast, 'ponteiro')"
          @mouseleave="soltar(toast, 'ponteiro')"
          @focusin="segurar(toast, 'foco')"
          @focusout="aoSairFoco($event, toast)"
        >
          <div class="min-w-0 flex-1">
            <p
              class="text-xs font-semibold"
              :class="CORES_NIVEL[toast.nivel]"
            >
              {{ ROTULOS_NIVEL[toast.nivel] }}
            </p>
            <p class="text-sm wrap-break-word text-texto">
              {{ toast.texto }}
            </p>
          </div>
          <button
            type="button"
            class="v8-btn v8-btn-icone text-texto-suave"
            aria-label="Dispensar"
            @click="toastStore.dispensar(toast.id)"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
<script setup>

// 1. Imports
import pinia from '~@/core/pinia'
import { useToastStore } from '~@/overlays/ToastStore'

// 2. Composables
const toastStore = useToastStore(pinia)

// 3. Props & Emits

// 4. State & Refs
// Nomes de classe completos, para que a varredura do Tailwind os encontre.
const CLASSES_NIVEL = {
  success: 'v8-toast-success',
  info: 'v8-toast-info',
  warning: 'v8-toast-warning',
  error: 'v8-toast-error'
}
const CORES_NIVEL = {
  success: 'text-sucesso',
  info: 'text-info',
  warning: 'text-aviso',
  error: 'text-perigo'
}
// O nível não é informado só pela cor.
const ROTULOS_NIVEL = {
  success: 'Sucesso',
  info: 'Informação',
  warning: 'Aviso',
  error: 'Erro'
}
// O que segura a contagem de cada toast: o ponteiro, o foco ou os dois (V8-OVL-071).
const motivos = new WeakMap()

// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks

// 8. Functions
function segurar(toast, motivo) {
  const ativos = motivos.get(toast) || new Set()
  ativos.add(motivo)
  motivos.set(toast, ativos)
  toastStore.pausar(toast.id)
}

function soltar(toast, motivo) {
  const ativos = motivos.get(toast)
  ativos?.delete(motivo)
  if (!ativos?.size) {
    toastStore.retomar(toast.id)
  }
}

function aoSairFoco(event, toast) {
  // O foco que só muda de lugar dentro do toast não retoma a contagem.
  if (event.relatedTarget && event.currentTarget.contains(event.relatedTarget)) {
    return
  }
  soltar(toast, 'foco')
}
</script>
