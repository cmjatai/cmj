<template>
  <table class="v8-tabela">
    <thead>
      <tr>
        <th scope="col">
          Número
        </th>
        <th scope="col">
          Descrição
        </th>
        <th scope="col">
          Data
        </th>
        <th scope="col">
          Valor
        </th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="pedido in pedidos"
        :key="pedido.id"
      >
        <td>{{ pedido.id }}</td>
        <td>
          <slot
            name="descricao"
            :pedido="pedido"
          >
            {{ pedido.descricao }}
          </slot>
        </td>
        <td>
          <time :datetime="pedido.data">{{ formatarData(pedido.data) }}</time>
        </td>
        <td>{{ formatarValor(pedido.valor) }}</td>
      </tr>
      <tr v-if="!pedidos.length">
        <td colspan="4">
          Nenhum pedido.
        </td>
      </tr>
    </tbody>
  </table>
</template>
<script setup>
// Pedidos de um cliente da demo. O slot `descricao` recebe { pedido } e permite trocar o texto
// da descrição por um link, como faz o detalhe da zona SPA.

// 1. Imports
import { formatarData, formatarValor } from '~@/modules/demo/formatos'

// 2. Composables
// 3. Props & Emits
defineProps({
  pedidos: {
    type: Array,
    default: () => []
  }
})

// 4. State & Refs
// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
