<template>
  <Teleport
    v-for="ilha in montadas"
    :key="ilha.chave"
    :to="ilha.el"
  >
    <component
      :is="ilha.componente"
      v-bind="ilha.props"
    />
  </Teleport>
</template>
<script setup>
// Monta as ilhas da página dentro do app único (V8-ARQ-033 a 035). Cada [data-vue-island]
// recebe, por Teleport, o componente registrado com aquele nome. O HTML que o Django pôs dentro
// do elemento fica no lugar até o componente estar pronto.

// 1. Imports
import { markRaw, onBeforeUnmount, onMounted, shallowRef } from 'vue'
import { ilhas } from '~@/core/ilhas'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  registro: {
    type: Object,
    default: () => ilhas
  }
})

// 4. State & Refs
const montadas = shallowRef([])
const vistas = new WeakSet()
let sequencia = 0
let observador = null

// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
onMounted(() => {
  procurar(document)
  // Ilhas em HTML que chega depois, como um fragmento num drawer, entram e saem sozinhas.
  observador = new MutationObserver(registros => {
    let removeu = false
    registros.forEach(registro => {
      registro.addedNodes.forEach(no => {
        if (no.nodeType === 1) {
          procurar(no)
        }
      })
      removeu = removeu || registro.removedNodes.length > 0
    })
    if (removeu && montadas.value.some(ilha => !ilha.el.isConnected)) {
      montadas.value = montadas.value.filter(ilha => ilha.el.isConnected)
    }
  })
  observador.observe(document.body, { childList: true, subtree: true })
})

onBeforeUnmount(() => observador?.disconnect())

// 8. Functions
function procurar(raiz) {
  if (raiz.matches?.('[data-vue-island]')) {
    montar(raiz)
  }
  raiz.querySelectorAll?.('[data-vue-island]').forEach(montar)
}

function lerProps(el) {
  const id = el.dataset.propsId
  const origem = id ? document.getElementById(id) : null
  if (!origem) {
    return {}
  }
  try {
    const dados = JSON.parse(origem.textContent)
    return dados && typeof dados === 'object' && !Array.isArray(dados) ? dados : {}
  } catch {
    return {}
  }
}

async function montar(el) {
  if (vistas.has(el)) {
    return
  }
  vistas.add(el)
  const nome = el.dataset.vueIsland
  // Só o registro decide o que é carregado: o nome nunca vira caminho (V8-ARQ-064).
  if (!Object.hasOwn(props.registro, nome)) {
    console.warn(`Ilha desconhecida: ${nome}`)
    return
  }
  try {
    const modulo = await props.registro[nome]()
    if (!el.isConnected) {
      return
    }
    const dados = lerProps(el)
    el.replaceChildren()
    el.setAttribute('data-vue-island-pronta', '')
    sequencia += 1
    montadas.value = [
      ...montadas.value,
      { chave: sequencia, el, componente: markRaw(modulo.default || modulo), props: dados }
    ]
  } catch (falha) {
    // O HTML do servidor continua no lugar (V8-ARQ-034).
    console.error(`Falha ao carregar a ilha ${nome}.`, falha)
  }
}
</script>
