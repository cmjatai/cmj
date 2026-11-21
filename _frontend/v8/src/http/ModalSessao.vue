<template>
  <div class="flex flex-col gap-3">
    <p class="v8-alerta v8-alerta-info">
      Sua sessão expirou. Entre novamente em outra aba e volte para cá: o que está nesta tela será
      mantido e o que ficou pendente será retomado.
    </p>
    <p
      v-if="aviso"
      role="status"
      data-sessao="aviso"
    >
      {{ aviso }}
    </p>
    <div class="v8-barra-acoes flex flex-wrap justify-end gap-2 mt-4">
      <button
        type="button"
        class="v8-btn v8-btn-fantasma"
        data-sessao="ir-login"
        @click="irParaLogin"
      >
        Ir para o login
      </button>
      <button
        type="button"
        class="v8-btn"
        data-sessao="ja-entrei"
        :disabled="verificando"
        @click="verificar(true)"
      >
        Já entrei
      </button>
      <button
        type="button"
        class="v8-btn v8-btn-primario"
        data-sessao="nova-aba"
        @click="entrarEmNovaAba"
      >
        Entrar em nova aba
      </button>
    </div>
  </div>
</template>
<script setup>
// Conteúdo do modal de sessão expirada (V8-HTTP-022). A autenticação acontece só na tela /login/,
// aberta em outra aba: este componente apenas consulta se a sessão voltou (V8-HTTP-043).

// 1. Imports
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { abrirNovaAba } from '~@/core/navegacao'
import pinia from '~@/core/pinia'
import http from '~@/http/client'
import { useOverlay } from '~@/overlays/useOverlay'
import { useGlobalStore } from '~@/stores/GlobalStore'

// 2. Composables
const overlay = useOverlay()
const globalStore = useGlobalStore(pinia)

// 3. Props & Emits

// 4. State & Refs
const verificando = ref(false)
const aviso = ref('')
let encerrado = false

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks
onMounted(() => {
  window.addEventListener('focus', aoVoltar)
  document.addEventListener('visibilitychange', aoVoltar)
})

onBeforeUnmount(() => {
  encerrado = true
  window.removeEventListener('focus', aoVoltar)
  document.removeEventListener('visibilitychange', aoVoltar)
})

// 8. Functions
function aoVoltar() {
  if (document.visibilityState !== 'hidden') {
    verificar(false)
  }
}

// Consulta /api/version. `pedida` é true quando o usuário clicou em "Já entrei": só nesse caso
// ele é avisado de que a sessão ainda não voltou.
async function verificar(pedida) {
  if (verificando.value || encerrado) {
    return
  }
  verificando.value = true
  let versao = null
  let falhou = false
  try {
    versao = await http.get(globalStore.urls.versao, { semSessao: true })
  } catch {
    falhou = true
  }
  verificando.value = false
  if (encerrado) {
    return
  }
  if (versao?.is_authenticated) {
    encerrado = true
    overlay.close({ retomar: true, versao })
    return
  }
  if (pedida) {
    aviso.value = falhou
      ? 'Não foi possível consultar o servidor. Tente novamente.'
      : 'Ainda não há sessão aberta. Entre pela nova aba e volte para cá.'
  }
}

function entrarEmNovaAba() {
  aviso.value = ''
  abrirNovaAba(globalStore.urls.login + '?next=' + encodeURIComponent(globalStore.urls.base))
}

function irParaLogin() {
  encerrado = true
  overlay.close({ retomar: false })
}
</script>
