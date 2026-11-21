<template>
  <ol
    class="v8-wizard-passos"
    aria-label="Passos"
  >
    <li
      v-for="(passo, i) in passos"
      :key="i"
      :aria-current="i === indice ? 'step' : undefined"
      :class="['v8-etiqueta', i === indice ? 'v8-etiqueta-ok' : 'v8-etiqueta-neutra']"
    >
      {{ i + 1 }}. {{ passo.titulo }}
    </li>
  </ol>

  <ErrosGerais :mensagens="gerais" />

  <form
    class="v8-wizard-corpo"
    @submit.prevent="avancar"
  >
    <component
      :is="componente"
      v-if="componente"
      :dados="dados"
      :erros="erros"
    />
    <div
      v-else
      class="v8-overlay-estado"
      role="status"
    >
      Carregando…
    </div>
    <button
      type="submit"
      hidden
    />
  </form>

  <OverlayFooter>
    <button
      type="button"
      class="v8-btn"
      :disabled="indice === 0 || enviando"
      data-wizard-voltar
      @click="voltar"
    >
      Voltar
    </button>
    <button
      type="button"
      class="v8-btn v8-btn-primario"
      :disabled="enviando || !componente"
      data-wizard-avancar
      @click="avancar"
    >
      {{ ultimo ? 'Concluir' : 'Avançar' }}
    </button>
  </OverlayFooter>
</template>
<script setup>
// Modal em passos (V8-OVL-066). Cada passo é { titulo, componente, validar }:
//   - `componente` (ou () => import(...)) recebe `dados` (objeto reativo comum a todos os passos,
//     que ele altera direto) e `erros` ({ campo: [mensagens] });
//   - `validar(dados)` devolve um objeto de erros por campo; vazio quer dizer válido.
// Ao concluir, `concluir(dados)` é chamado, se houver, e o modal resolve com o que ele devolver
// ou com os dados reunidos.

// 1. Imports
import { computed, markRaw, reactive, ref, shallowRef, watch } from 'vue'
import { HttpError } from '~@/http/client'
import { useOverlay } from '~@/overlays/useOverlay'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import ErrosGerais from '~@/overlays/ErrosGerais.vue'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
const props = defineProps({
  passos: {
    type: Array,
    required: true
  },
  dadosIniciais: {
    type: Object,
    default: () => ({})
  },
  concluir: {
    type: Function,
    default: null
  }
})

// 4. State & Refs
const indice = ref(0)
const dados = reactive({ ...props.dadosIniciais })
const erros = ref({})
const gerais = ref([])
const enviando = ref(false)
const componente = shallowRef(null)

// 5. Computed Properties
const ultimo = computed(() => indice.value === props.passos.length - 1)

// 6. Watchers
watch(dados, () => overlay.setDirty(true), { deep: true })
watch(indice, carregarPasso, { immediate: true })

// 7. Events & Lifecycle Hooks
// 8. Functions
function ehCarregador(valor) {
  return typeof valor === 'function' && !valor.render && !valor.setup && !valor.__vccOpts
}

async function carregarPasso() {
  const alvo = props.passos[indice.value]?.componente
  componente.value = null
  if (!alvo) {
    return
  }
  if (!ehCarregador(alvo)) {
    componente.value = markRaw(alvo)
    return
  }
  const posicao = indice.value
  const modulo = await alvo()
  if (posicao === indice.value) {
    componente.value = markRaw(modulo.default || modulo)
  }
}

function comoListas(resultado) {
  const saida = {}
  Object.entries(resultado || {}).forEach(([campo, valor]) => {
    const lista = Array.isArray(valor) ? valor : [valor]
    if (lista.filter(Boolean).length) {
      saida[campo] = lista.filter(Boolean)
    }
  })
  return saida
}

async function passoValido() {
  const validar = props.passos[indice.value]?.validar
  erros.value = validar ? comoListas(await validar(dados)) : {}
  return !Object.keys(erros.value).length
}

function voltar() {
  if (indice.value > 0) {
    erros.value = {}
    gerais.value = []
    indice.value -= 1
  }
}

async function avancar() {
  if (enviando.value || !componente.value) {
    return
  }
  gerais.value = []
  if (!(await passoValido())) {
    return
  }
  if (!ultimo.value) {
    indice.value += 1
    return
  }
  enviando.value = true
  try {
    const resposta = props.concluir ? await props.concluir({ ...dados }) : undefined
    overlay.setDirty(false)
    overlay.close(resposta === undefined ? { ...dados } : resposta)
  } catch (falha) {
    if (falha instanceof HttpError && falha.codigo === 'validacao') {
      erros.value = falha.campos || {}
      gerais.value = [...(falha.gerais || [])]
      Object.entries(erros.value).forEach(([campo, mensagens]) => {
        gerais.value.push(`${campo}: ${mensagens.join(' ')}`)
      })
    } else {
      gerais.value = [falha?.mensagem || 'Não foi possível concluir. Tente de novo.']
    }
  } finally {
    enviando.value = false
  }
}
</script>
