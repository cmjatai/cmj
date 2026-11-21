<template>
  <EstadoCarga
    v-if="!cliente"
    :carregando="carregando"
    :erro="erro"
    @tentar="carregar"
  />
  <dl
    v-else-if="item"
    class="v8-lista-dados"
  >
    <dt>Número</dt>
    <dd>{{ item.id }}</dd>
    <dt>Descrição</dt>
    <dd>{{ item.descricao }}</dd>
    <dt>Data</dt>
    <dd>
      <time :datetime="item.data">{{ formatarData(item.data) }}</time>
    </dd>
    <dt>Valor</dt>
    <dd>{{ formatarValor(item.valor) }}</dd>
    <dt>Cliente</dt>
    <dd>{{ cliente.nome }}</dd>
  </dl>
  <div
    v-else
    class="v8-overlay-estado"
    role="alert"
  >
    <p>Este cliente não tem o pedido {{ pedido }}.</p>
  </div>
</template>
<script setup>
// Pedido de um cliente na zona SPA (V8-DEMO-021): rota filha do detalhe, desenhada num segundo
// drawer, empilhado. A API da demo não tem endereço de pedido: ele vem junto com o cliente.

// 1. Imports
import { computed, watch } from 'vue'
import { useOverlay } from '~@/overlays/useOverlay'
import EstadoCarga from '~@/modules/demo/componentes/EstadoCarga.vue'
import { formatarData, formatarValor } from '~@/modules/demo/formatos'
import { useCliente } from '~@/modules/demo/useCliente'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
const props = defineProps({
  id: {
    type: Number,
    required: true
  },
  pedido: {
    type: Number,
    required: true
  }
})

// 4. State & Refs
const { cliente, carregando, erro, carregar } = useCliente(() => props.id)

// 5. Computed Properties
const item = computed(() => cliente.value?.pedidos?.find(p => p.id === props.pedido) || null)

// 6. Watchers
watch(item, valor => {
  if (valor) {
    overlay.setTitle(`Pedido ${valor.id}`)
  }
})

// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
