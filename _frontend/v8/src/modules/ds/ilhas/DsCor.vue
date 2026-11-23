<template>
  <div class="grid gap-8 lg:grid-cols-2">
    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">AreaCor, DeslizanteCor, CampoCor</code>
      <AreaCor
        v-model="cor"
        rotulo="Saturação e brilho"
      />
      <DeslizanteCor
        v-model="cor"
        canal="hue"
      />
      <CampoCor
        v-model="cor"
        rotulo="Cor em hexadecimal"
      />
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">AmostraCor, PaletaCores</code>
      <div class="flex flex-wrap items-center gap-2">
        <AmostraCor
          v-for="token in tokens"
          :key="token.rotulo"
          :cor="token.valor"
          :rotulo="token.rotulo"
          tamanho="lg"
        />
      </div>
      <PaletaCores
        v-model="cor"
        rotulo="Cores do tema"
        :opcoes="tokens"
      />
      <p
        class="text-sm text-texto-suave"
        data-ds-cor
      >
        {{ cor }}
      </p>
    </div>
  </div>
</template>

<script setup>
// Ilha `ds-cor` da vitrine (V8-DS-018): os componentes de cor de componentes.md. As cores de
// amostra são lidas dos tokens do tema e do modo em vigor, sem cor escrita no código (V8-CMP-035).
// Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { onMounted, ref } from 'vue'
import AmostraCor from '~@/componentes/AmostraCor.vue'
import AreaCor from '~@/componentes/AreaCor.vue'
import CampoCor from '~@/componentes/CampoCor.vue'
import DeslizanteCor from '~@/componentes/DeslizanteCor.vue'
import PaletaCores from '~@/componentes/PaletaCores.vue'

// 4. State & Refs
const NOMES = ['primaria', 'realce', 'info', 'sucesso', 'aviso', 'perigo', 'topo']
const tokens = ref([])
const cor = ref(undefined)

// 7. Events & Lifecycle Hooks
onMounted(() => {
  tokens.value = lerTokens()
  cor.value = tokens.value[0]?.valor
})

// 8. Functions
// Os tokens `--cor-*` em vigor que estão em hexadecimal, o formato dos componentes de cor.
function lerTokens() {
  const estilo = window.getComputedStyle(document.documentElement)
  return NOMES.map(nome => ({ rotulo: `--cor-${nome}`, valor: estilo.getPropertyValue(`--cor-${nome}`).trim().toLowerCase() }))
    .filter(token => /^#([0-9a-f]{3}|[0-9a-f]{6})$/.test(token.valor))
    .map(token => ({ ...token, valor: token.valor.length === 4 ? expandir(token.valor) : token.valor }))
}

function expandir(curto) {
  return `#${[...curto.slice(1)].map(digito => digito + digito).join('')}`
}
</script>
