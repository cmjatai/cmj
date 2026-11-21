<template>
  <div class="v8-barra-acoes">
    <button
      type="button"
      class="v8-btn v8-btn-primario"
      @click="novoCliente"
    >
      Novo cliente
    </button>
    <button
      type="button"
      class="v8-btn"
      :disabled="testando"
      @click="testarAcessoNegado"
    >
      Testar acesso negado
    </button>
  </div>

  <form
    role="search"
    class="v8-campo"
    @submit.prevent="buscarAgora"
  >
    <label
      class="v8-rotulo"
      :for="idDaBusca"
    >Nome ou e-mail</label>
    <input
      :id="idDaBusca"
      v-model="q"
      class="v8-entrada"
      type="search"
      maxlength="100"
      autocomplete="off"
    >
  </form>

  <EstadoCarga
    v-if="!resultado"
    :carregando="carregando"
    :erro="erro"
    @tentar="carregar"
  />
  <template v-else>
    <p
      class="mb-2 text-sm text-texto-suave"
      aria-live="polite"
    >
      {{ encontrados }}
    </p>
    <table
      class="v8-tabela"
      :aria-busy="carregando ? 'true' : undefined"
    >
      <thead>
        <tr>
          <th scope="col">
            Nome
          </th>
          <th scope="col">
            E-mail
          </th>
          <th scope="col">
            Cidade
          </th>
          <th scope="col">
            Situação
          </th>
          <th scope="col">
            Pedidos
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="cliente in resultado.itens"
          :key="cliente.id"
        >
          <td>
            <RouterLink :to="{ name: 'demo_spa_cliente', params: { id: cliente.id } }">
              {{ cliente.nome }}
            </RouterLink>
          </td>
          <td>{{ cliente.email }}</td>
          <td>{{ cliente.cidade }}</td>
          <td>
            <EtiquetaSituacao :situacao="cliente.situacao" />
          </td>
          <td>{{ cliente.total_pedidos }}</td>
        </tr>
        <tr v-if="!resultado.itens.length">
          <td colspan="5">
            Nenhum cliente encontrado.
          </td>
        </tr>
      </tbody>
    </table>
    <nav
      v-if="resultado.paginas > 1"
      class="v8-paginacao"
      aria-label="Paginação"
    >
      <button
        type="button"
        class="v8-btn"
        :disabled="carregando || resultado.pagina <= 1"
        @click="irParaPagina(resultado.pagina - 1)"
      >
        Anterior
      </button>
      <span>Página {{ resultado.pagina }} de {{ resultado.paginas }}</span>
      <button
        type="button"
        class="v8-btn"
        :disabled="carregando || resultado.pagina >= resultado.paginas"
        @click="irParaPagina(resultado.pagina + 1)"
      >
        Próxima
      </button>
    </nav>
  </template>

  <DrawerRota />
</template>
<script setup>
// Lista de clientes da zona SPA (V8-DEMO-020), carregada da API da demo. O nome leva à rota
// filha do detalhe, que o <DrawerRota> desenha num drawer sobre a lista (V8-DEMO-021).
//
// A barra de ações mostra o modal `wizard` (V8-DEMO-023) e o tratamento de uma resposta 403
// (V8-DEMO-025): o cliente HTTP só entrega o erro, e é a tela que decide mostrar o toast.

// 1. Imports
import { computed, onBeforeUnmount, ref, shallowRef, useId, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { HttpError } from '~@/http/client'
import DrawerRota from '~@/overlays/DrawerRota.vue'
import { useModal } from '~@/overlays/useModal'
import { useToast } from '~@/overlays/useToast'
import * as api from '~@/modules/demo/api'
import EstadoCarga from '~@/modules/demo/componentes/EstadoCarga.vue'
import EtiquetaSituacao from '~@/modules/demo/componentes/EtiquetaSituacao.vue'
import { dadosIniciais, passosNovoCliente } from '~@/modules/demo/wizard/passos'

// 2. Composables
const modal = useModal()
const toast = useToast()
const idDaBusca = useId()

// 3. Props & Emits
// 4. State & Refs
const ATRASO_DA_BUSCA = 300
const q = ref('')
const pagina = ref(1)
const resultado = shallowRef(null)
const carregando = ref(false)
const erro = shallowRef(null)
const testando = ref(false)
// Só a resposta do pedido mais recente vale: a busca pode mudar com um pedido em curso.
let pedido = 0
const buscarComAtraso = _.debounce(buscar, ATRASO_DA_BUSCA)

// 5. Computed Properties
const encontrados = computed(() => {
  const total = resultado.value?.total || 0
  return total === 1 ? '1 cliente encontrado.' : `${total} clientes encontrados.`
})

// 6. Watchers
watch(q, () => buscarComAtraso())

// 7. Events & Lifecycle Hooks
onBeforeUnmount(() => buscarComAtraso.cancel())

carregar()

// 8. Functions
async function carregar() {
  pedido += 1
  const atual = pedido
  erro.value = null
  carregando.value = true
  try {
    const resposta = await api.listar({ q: q.value.trim(), pagina: pagina.value })
    if (atual === pedido) {
      resultado.value = resposta
      // O servidor traz a página pedida para o intervalo que existe.
      pagina.value = resposta.pagina
    }
  } catch (falha) {
    if (atual === pedido) {
      resultado.value = null
      erro.value = falha
    }
  } finally {
    if (atual === pedido) {
      carregando.value = false
    }
  }
}

function buscar() {
  pagina.value = 1
  return carregar()
}

// Enter na caixa de busca não espera o atraso.
function buscarAgora() {
  buscarComAtraso.cancel()
  return buscar()
}

function irParaPagina(numero) {
  pagina.value = numero
  return carregar()
}

async function novoCliente() {
  const criado = await modal.openWizard({
    title: 'Novo cliente',
    passos: passosNovoCliente,
    dados: dadosIniciais(),
    concluir: dados => api.criar(dados)
  })
  // Wizard dispensado resolve com undefined.
  if (criado) {
    toast.success(`Cliente ${criado.nome} criado. Demonstração: nada foi gravado.`)
  }
}

async function testarAcessoNegado() {
  testando.value = true
  try {
    await api.negado()
    toast.warning('A requisição foi aceita, e a demonstração esperava uma recusa.')
  } catch (falha) {
    if (falha instanceof HttpError && falha.codigo === 'sem_permissao') {
      // É o resultado esperado: o servidor recusou, e a mensagem vem do próprio erro.
      toast.error(falha.mensagem)
    } else {
      toast.warning(`O teste não chegou à recusa do servidor. ${falha?.mensagem || ''}`.trim())
    }
  } finally {
    testando.value = false
  }
}
</script>
