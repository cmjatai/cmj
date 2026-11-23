<template>
  <ToolbarRoot
    class="v8-barra-ferramentas"
    :aria-label="rotulo || undefined"
  >
    <template
      v-for="(item, posicao) in itens"
      :key="item.valor ?? `${posicao}`"
    >
      <ToolbarSeparator
        v-if="item.separador"
        class="v8-barra-ferramentas-separador"
      />
      <ToolbarLink
        v-else-if="item.href"
        class="v8-btn v8-btn-fantasma"
        :href="item.href"
      >
        {{ item.rotulo }}
      </ToolbarLink>
      <ToolbarButton
        v-else
        class="v8-btn v8-btn-fantasma"
        :disabled="item.desabilitado"
        @click="emit('acionar', item.valor)"
      >
        {{ item.rotulo }}
      </ToolbarButton>
    </template>
    <template v-if="alternadores.length">
      <ToolbarSeparator
        v-if="itens.length"
        class="v8-barra-ferramentas-separador"
      />
      <ToolbarToggleGroup
        v-model="valor"
        class="v8-grupo-alternadores"
        :type="multiplo ? 'multiple' : 'single'"
      >
        <ToolbarToggleItem
          v-for="alternador in alternadores"
          :key="alternador.valor"
          class="v8-btn v8-alternador"
          :value="alternador.valor"
          :disabled="alternador.desabilitado"
          :aria-label="alternador.rotuloAcessivel || undefined"
        >
          {{ alternador.rotulo }}
        </ToolbarToggleItem>
      </ToolbarToggleGroup>
    </template>
  </ToolbarRoot>
</template>

<script setup>
// Barra de ferramentas (docs/specs/v8/componentes.md), sobre o Toolbar do Reka UI: botões, links e
// separadores (`itens`) e, no fim, um grupo de alternadores (`alternadores`) cujo valor vai no
// v-model. Item é `{ valor, rotulo, desabilitado }`, `{ rotulo, href }` ou `{ separador: true }`;
// clicar num botão emite `acionar` com o valor.
//
//   <BarraFerramentas rotulo="Formatação" :itens="acoes" :alternadores="estilos" v-model="estilo" @acionar="executar" />

// 1. Imports
import { ToolbarButton, ToolbarLink, ToolbarRoot, ToolbarSeparator, ToolbarToggleGroup, ToolbarToggleItem } from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    default: () => []
  },
  alternadores: {
    type: Array,
    default: () => []
  },
  multiplo: {
    type: Boolean,
    default: false
  },
  rotulo: {
    type: String,
    default: ''
  }
})
const emit = defineEmits(['acionar'])
const valor = defineModel({ type: [String, Array], default: undefined })
</script>
