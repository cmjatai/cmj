<template>
  <EstadoCarga
    v-if="!cliente"
    :carregando="carregando"
    :erro="erro"
    @tentar="carregar"
  />
  <template v-else>
    <h3 class="mb-4 text-xl font-semibold">
      {{ cliente.nome }}
    </h3>
    <section class="v8-cartao">
      <ClienteDados :cliente="cliente" />
    </section>
    <h4 class="mt-4 mb-2 font-semibold">
      Pedidos
    </h4>
    <PedidosTabela :pedidos="cliente.pedidos" />
    <p class="mt-2 text-sm text-texto-suave">
      {{ totais }}
    </p>
  </template>
  <OverlayFooter>
    <button
      type="button"
      class="v8-btn v8-btn-primario"
      @click="overlay.close()"
    >
      Fechar
    </button>
  </OverlayFooter>
</template>
<script setup>
// Resumo do cliente, conteúdo do modal de tela cheia (V8-DEMO-024). É aberto por
// data-modal="demo-resumo:<id>" na página Django e por openFullscreen() na zona SPA.

// 1. Imports
import { computed } from 'vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useOverlay } from '~@/overlays/useOverlay'
import ClienteDados from '~@/modules/demo/componentes/ClienteDados.vue'
import EstadoCarga from '~@/modules/demo/componentes/EstadoCarga.vue'
import PedidosTabela from '~@/modules/demo/componentes/PedidosTabela.vue'
import { formatarValor } from '~@/modules/demo/formatos'
import { useCliente } from '~@/modules/demo/useCliente'

// 2. Composables
const overlay = useOverlay()

// 3. Props & Emits
const props = defineProps({
  id: {
    type: Number,
    required: true
  }
})

// 4. State & Refs
const { cliente, carregando, erro, carregar } = useCliente(() => props.id)

// 5. Computed Properties
const totais = computed(() => {
  const pedidos = cliente.value?.pedidos || []
  const soma = _.sumBy(pedidos, pedido => Number(pedido.valor) || 0)
  const quantos = pedidos.length === 1 ? '1 pedido' : `${pedidos.length} pedidos`
  return `${quantos}, total de ${formatarValor(soma)}.`
})

// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
