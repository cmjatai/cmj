<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted small py-3 text-center">
      Nenhum documento acessório encontrado para a matéria vinculada.
    </div>
    <b-table v-else
      :items="items"
      :fields="fields"
      small striped hover
      class="mb-0 text-center"
    >
      <template #cell(nome)="data">
        <a v-if="data.value && data.item.link_detail_backend"
           :href="data.item.link_detail_backend"
           target="_blank"
           class="small">
          {{ data.value.__str__ || data.value }}
        </a>
        <span v-else class="small">{{ data.value ? (data.value.__str__ || data.value) : '—' }}</span>
      </template>
      <template #cell(tipo)="data">
        <span class="small">{{ data.value ? (data.value.__str__ || data.value) : '—' }}</span>
      </template>
      <template #cell(data)="data">
        <span class="small">{{ formatDateBR(data.value) }}</span>
      </template>
      <template #cell(autor)="data">
        <span class="small">{{ data.value || '—' }}</span>
      </template>
      <template #cell(arquivo)="data">
        <a v-if="data.value" :href="data.value" target="_blank" class="btn btn-sm btn-outline-secondary">
          <i class="fas fa-download mr-1"></i>Baixar
        </a>
        <span v-else class="small">—</span>
      </template>
    </b-table>
  </div>
</template>

<script>
import { formatDateBR } from '../utils/pcl-helpers'

export default {
  name: 'pcl-tab-documentos',
  props: {
    items: {
      type: Array,
      default: null
    }
  },
  computed: {
    fields () {
      return [
        { key: 'nome', label: 'Nome' },
        { key: 'tipo', label: 'Tipo' },
        { key: 'data', label: 'Data' },
        { key: 'autor', label: 'Autor' },
        { key: 'arquivo', label: 'Arquivo' }
      ]
    }
  },
  methods: {
    formatDateBR
  }
}
</script>
