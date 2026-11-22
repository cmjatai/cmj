<template>
  <TabsRoot
    v-model="valor"
    class="v8-abas"
    :default-value="itens[0]?.valor"
  >
    <TabsList
      class="v8-abas-lista"
      :aria-label="rotulo"
    >
      <TabsTrigger
        v-for="item in itens"
        :key="item.valor"
        class="v8-abas-gatilho"
        :value="item.valor"
        :disabled="item.desabilitado"
      >
        {{ item.rotulo }}
      </TabsTrigger>
    </TabsList>
    <TabsContent
      v-for="item in itens"
      :key="item.valor"
      class="v8-abas-painel"
      :value="item.valor"
    >
      <slot
        :name="item.valor"
        :item="item"
      />
    </TabsContent>
  </TabsRoot>
</template>

<script setup>
// Abas (docs/specs/v8/componentes.md): painéis alternados na mesma área, sobre o Tabs do Reka UI.
//
//   <Abas v-model="aba" rotulo="Dados" :itens="[{ valor: 'geral', rotulo: 'Geral' }]">
//     <template #geral>...</template>
//   </Abas>

// 1. Imports
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from 'reka-ui'

// 3. Props & Emits
defineProps({
  itens: {
    type: Array,
    required: true
  },
  rotulo: {
    type: String,
    default: ''
  }
})
const valor = defineModel({ type: String, default: undefined })
</script>
