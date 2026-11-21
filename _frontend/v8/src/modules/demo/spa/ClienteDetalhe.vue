<template>
  <EstadoCarga
    v-if="!cliente"
    :carregando="carregando"
    :erro="erro"
    @tentar="carregar"
  />
  <template v-else>
    <ClienteDados :cliente="cliente" />
    <h3 class="mt-4 mb-2 font-semibold">
      Pedidos
    </h3>
    <PedidosTabela :pedidos="cliente.pedidos">
      <template #descricao="{ pedido }">
        <RouterLink :to="{ name: 'demo_spa_pedido', params: { id, pedido: pedido.id } }">
          {{ pedido.descricao }}
        </RouterLink>
      </template>
    </PedidosTabela>
    <OverlayFooter>
      <button
        type="button"
        class="v8-btn v8-btn-primario"
        @click="editar"
      >
        Editar
      </button>
      <button
        type="button"
        class="v8-btn"
        @click="ampliar"
      >
        Ampliar
      </button>
    </OverlayFooter>
  </template>

  <DrawerRota />
</template>
<script setup>
// Detalhe do cliente na zona SPA (V8-DEMO-021). É uma rota filha da lista, desenhada num drawer
// pelo <DrawerRota> de ClientesLista.vue. O <DrawerRota> daqui faz o mesmo com a rota do pedido,
// que abre empilhada sobre este drawer.
//
// "Editar" abre o modal `form` e espera o resultado dele (V8-DEMO-022). "Ampliar" abre o modal
// de tela cheia (V8-DEMO-024).

// 1. Imports
import { watch } from 'vue'
import { RouterLink } from 'vue-router'
import DrawerRota from '~@/overlays/DrawerRota.vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useModal } from '~@/overlays/useModal'
import { useOverlay } from '~@/overlays/useOverlay'
import { useToast } from '~@/overlays/useToast'
import ClienteDados from '~@/modules/demo/componentes/ClienteDados.vue'
import EstadoCarga from '~@/modules/demo/componentes/EstadoCarga.vue'
import PedidosTabela from '~@/modules/demo/componentes/PedidosTabela.vue'
import { useCliente } from '~@/modules/demo/useCliente'

// 2. Composables
const modal = useModal()
const overlay = useOverlay()
const toast = useToast()

// 3. Props & Emits
const props = defineProps({
  id: {
    type: Number,
    required: true
  }
})

// 4. State & Refs
// O drawer é o mesmo ao trocar de cliente: o id muda e o cliente é carregado de novo.
const { cliente, carregando, erro, carregar } = useCliente(() => props.id)

// 5. Computed Properties
// 6. Watchers
// Sem cliente carregado, o título volta ao de `meta.drawer` da rota.
watch(cliente, valor => overlay.setTitle(valor?.nome || 'Cliente'))

// 7. Events & Lifecycle Hooks
// 8. Functions
async function editar() {
  const editado = cliente.value
  const salvo = await modal.openForm(
    () => import('~@/modules/demo/modais/ClienteForm.vue'),
    { cliente: { ...editado } },
    { title: 'Editar cliente' }
  )
  // Modal dispensado resolve com undefined.
  if (!salvo) {
    return
  }
  // A resposta é o cliente como ficaria gravado. Vale só se ele ainda é o que está na tela.
  if (cliente.value?.id === editado.id) {
    cliente.value = { ...cliente.value, ...salvo }
  }
  toast.success('Cliente salvo. Demonstração: nada foi gravado.')
}

function ampliar() {
  return modal.openFullscreen(
    () => import('~@/modules/demo/modais/ClienteResumo.vue'),
    { id: props.id },
    { title: 'Resumo do cliente' }
  )
}
</script>
