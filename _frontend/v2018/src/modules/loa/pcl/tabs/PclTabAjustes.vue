<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted small py-3 text-center">
      Nenhum ajuste vinculado a esta emenda.
    </div>
    <b-table v-else
      :items="items"
      :fields="fields"
      small striped hover
      class="mb-0"
    >
      <template #cell(str_valor)="data">
        <span class="text-nowrap">R$ {{ data.value }}</span>
      </template>
      <template #cell(descricao)="data">
        <a :href="data.item.link_detail_backend" target="_blank" class="small">{{ data.value }}</a>
      </template>
      <template #cell(oficio_ajuste_loa)="data">
        <a v-if="data.value && data.value.link_detail_backend"
          :href="data.value.link_detail_backend"
          target="_blank"
          class="btn btn-sm btn-outline-secondary"
          title="Abrir ofício"
        >
          <i class="fas fa-external-link-alt mr-1"></i>{{ data.value.__str__ || 'Ofício' }}
        </a>
        <span v-else class="small">{{ data.value ? data.value.__str__ : '—' }}</span>
      </template>
    </b-table>
  </div>
</template>

<script>
export default {
  name: 'pcl-tab-ajustes',
  props: {
    items: {
      type: Array,
      default: null
    }
  },
  computed: {
    fields () {
      return [
        { key: 'str_valor', label: 'Valor' },
        { key: 'descricao', label: 'Descrição' },
        { key: 'oficio_ajuste_loa', label: 'Ofício' }
      ]
    }
  }
}
</script>
