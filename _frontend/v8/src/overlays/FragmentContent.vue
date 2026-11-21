<template>
  <div
    v-if="erro"
    class="v8-overlay-estado"
    role="alert"
  >
    <p>{{ erro }}</p>
    <button
      type="button"
      class="v8-btn"
      @click="carregar"
    >
      Tentar de novo
    </button>
  </div>
  <div
    v-else-if="carregando"
    class="v8-overlay-estado"
    role="status"
  >
    Carregando…
  </div>
  <div
    v-show="!erro && !carregando"
    ref="raiz"
    class="v8-fragmento"
  />
</template>
<script setup>
// Fragmento HTML servido pelo Django em /v8/_frag/<caminho>/ (V8-OVL-040, 042 e 103).
//
// O HTML entra por innerHTML, que não executa <script>. As ilhas e os gatilhos dentro dele são
// atendidos pelo IslandHost e pela delegação de cliques, que observam o documento.

// 1. Imports
import { onMounted, ref } from 'vue'
import pinia from '~@/core/pinia'
import http from '~@/http/client'
import { useGlobalStore } from '~@/stores/GlobalStore'
import { urlDoFragmento } from '~@/overlays/alvo'
import { useOverlay } from '~@/overlays/useOverlay'

// 2. Composables
const overlay = useOverlay()
const global = useGlobalStore(pinia)

// 3. Props & Emits
const props = defineProps({
  caminho: {
    type: String,
    required: true
  }
})

// 4. State & Refs
const raiz = ref(null)
const carregando = ref(true)
const erro = ref('')

// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
onMounted(carregar)

// 8. Functions
async function carregar() {
  const url = urlDoFragmento(props.caminho, global.urls.frag)
  erro.value = ''
  if (!url) {
    carregando.value = false
    erro.value = 'Endereço de fragmento inválido.'
    return
  }
  carregando.value = true
  try {
    const html = await http.get(url, { accept: 'html' })
    raiz.value.innerHTML = typeof html === 'string' ? html : ''
    const titulo = raiz.value.querySelector('[data-overlay-title]')?.textContent?.trim()
    if (titulo) {
      overlay.setTitle(titulo)
    }
  } catch (falha) {
    erro.value = falha?.mensagem || 'Não foi possível carregar este conteúdo.'
  } finally {
    carregando.value = false
  }
}
</script>
