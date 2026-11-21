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
    <PedidosTabela :pedidos="cliente.pedidos" />
    <OverlayFooter>
      <a
        class="v8-btn"
        :href="'/v8/_frag/demo/cliente/' + id + '/historico/'"
        :data-drawer="'frag:demo/cliente/' + id + '/historico'"
        data-drawer-side="right"
      >Histórico</a>
      <a
        class="v8-btn"
        :href="'/v8/demo/clientes/' + id + '/'"
        :data-modal="'demo-resumo:' + id"
      >Ampliar</a>
      <button
        type="button"
        class="v8-btn"
        @click="copiarEmail"
      >
        Copiar e-mail
      </button>
    </OverlayFooter>
  </template>
</template>
<script setup>
// Conteúdo do drawer aberto por ?painel=cliente:<id> na página Django da demo (V8-DEMO-013).
//
// "Histórico" e "Ampliar" são links comuns com data-drawer e data-modal: o ouvinte de cliques do
// documento abre o segundo drawer, empilhado, com o fragmento do servidor (V8-DEMO-014), e o
// modal de tela cheia. Sem JavaScript, os mesmos links levam ao fragmento e à página de detalhe.

// 1. Imports
import { watch } from 'vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useOverlay } from '~@/overlays/useOverlay'
import { useToast } from '~@/overlays/useToast'
import ClienteDados from '~@/modules/demo/componentes/ClienteDados.vue'
import EstadoCarga from '~@/modules/demo/componentes/EstadoCarga.vue'
import PedidosTabela from '~@/modules/demo/componentes/PedidosTabela.vue'
import { useCliente } from '~@/modules/demo/useCliente'

// 2. Composables
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
const { cliente, carregando, erro, carregar } = useCliente(() => props.id)

// 5. Computed Properties
// 6. Watchers
watch(cliente, valor => {
  if (valor) {
    overlay.setTitle(valor.nome)
  }
})

// 7. Events & Lifecycle Hooks
// 8. Functions
async function copiar(texto) {
  // A área de transferência só existe em contexto seguro (HTTPS ou localhost).
  if (!navigator.clipboard?.writeText) {
    return false
  }
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    return false
  }
}

async function copiarEmail() {
  const email = cliente.value.email
  if (await copiar(email)) {
    toast.success('E-mail copiado.')
  } else {
    toast.info(`Não foi possível copiar. O e-mail é ${email}`)
  }
}
</script>
