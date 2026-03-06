<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div
      v-else-if="items.length === 0"
      class="text-muted small py-3 text-center"
    >
      Nenhuma tramitação encontrada para a matéria vinculada.
    </div>
    <b-table
      v-else
      :items="items"
      :fields="fields"
      small
      striped
      hover
      class="mb-0"
    >
      <template #cell(data_tramitacao)="data">
        <a v-if="data.value && data.item.link_detail_backend"
           :href="data.item.link_detail_backend"
           target="_blank"
           class="small text-center d-block">
         {{ formatDateBR(data.value) }}
        </a>
      </template>
      <template #cell(data_fim_prazo)="data">
        <span class="small">{{ formatDateBR(data.value) }}</span>
      </template>
      <template #cell(status)="data">
        <span class="small">{{
          data.value ? data.value.__str__ || data.value : "—"
        }}</span>
      </template>
      <template #cell(unidade_tramitacao_destino)="data">
        <span class="small">{{
          data.value ? data.value.__str__ || data.value : "—"
        }}</span>
      </template>
      <template #cell(texto)="data">
        <span class="small">{{
          data.value ? data.value.__str__ || data.value : "—"
        }}</span>
      </template>
    </b-table>
  </div>
</template>

<script>
import { formatDateBR } from '../utils/pcl-helpers'

export default {
  name: 'pcl-tab-tramitacoes',
  props: {
    items: {
      type: Array,
      default: null
    }
  },
  computed: {
    fields () {
      return [
        { key: 'data_tramitacao', label: 'Data Tramitação' },
        { key: 'data_fim_prazo', label: 'Fim Prazo' },
        { key: 'unidade_tramitacao_destino', label: 'Destino' },
        { key: 'status', label: 'Status' },
        { key: 'texto', label: 'Texto' }
      ]
    }
  },
  methods: {
    formatDateBR
  }
}
</script>
