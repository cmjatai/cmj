<template>
  <div>
    <table class="v8-tabela">
      <thead>
        <tr>
          <th scope="col">
            <input
              type="checkbox"
              aria-label="Selecionar todos"
              :checked="todos"
              :indeterminate="alguns"
              :disabled="!clientes.length"
              @change="alternarTodos"
            >
          </th>
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
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="cliente in clientes"
          :key="cliente.id"
        >
          <td>
            <input
              v-model="selecionados"
              type="checkbox"
              name="ids"
              :value="cliente.id"
              :form="formulario || undefined"
              :aria-label="'Selecionar ' + cliente.nome"
            >
          </td>
          <td>
            <a
              :href="'/v8/demo/clientes/' + cliente.id + '/'"
              :data-drawer="'cliente:' + cliente.id"
              data-drawer-side="right"
            >{{ cliente.nome }}</a>
          </td>
          <td>{{ cliente.email }}</td>
          <td>{{ cliente.cidade }}</td>
          <td>
            <EtiquetaSituacao :situacao="cliente.situacao" />
          </td>
        </tr>
        <tr v-if="!clientes.length">
          <td colspan="5">
            Nenhum cliente encontrado com estes filtros.
          </td>
        </tr>
      </tbody>
    </table>
    <p
      class="mt-2 text-sm text-texto-suave"
      aria-live="polite"
    >
      {{ contagem }}
    </p>
  </div>
</template>
<script setup>
// Ilha `demo-clientes-tabela` (V8-DEMO-011). Substitui a tabela que o Django desenhou por uma
// igual e acrescenta "selecionar todos" e a contagem dos selecionados.
//
// As caixas de seleção continuam pertencendo ao formulário de ação em massa que o Django desenha
// fora da ilha: é o atributo `form` que faz os ids marcados irem no envio dele. O nome é um link
// comum com data-drawer: quem abre o drawer é o ouvinte de cliques do documento (V8-OVL-080).

// 1. Imports
import { computed, ref } from 'vue'
import EtiquetaSituacao from '~@/modules/demo/componentes/EtiquetaSituacao.vue'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  // Itens da página atual da lista: { id, nome, email, cidade, situacao }.
  clientes: {
    type: Array,
    default: () => []
  },
  // Id do <form> da ação em massa.
  formulario: {
    type: String,
    default: ''
  }
})

// 4. State & Refs
const selecionados = ref([])

// 5. Computed Properties
const todos = computed(() => props.clientes.length > 0 && selecionados.value.length === props.clientes.length)
const alguns = computed(() => selecionados.value.length > 0 && !todos.value)
const contagem = computed(() => {
  const total = selecionados.value.length
  return total === 1 ? '1 selecionado' : `${total} selecionados`
})

// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
function alternarTodos(evento) {
  selecionados.value = evento.target.checked ? props.clientes.map(cliente => cliente.id) : []
}
</script>
