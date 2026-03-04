<template>
  <div>
    <div v-if="items === null" class="text-center py-3">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted text-center py-3">
      Nenhum registro de prestação de contas encontrado.
      <div v-if="registro && registro.emendaloa">
        Verifique na Emenda Vinculada a Prestação de Contas.
      </div>
    </div>
    <b-table v-else
      :items="items"
      :fields="fields"
      :sort-by.sync="localSortBy"
      :sort-desc.sync="localSortDesc"
      small striped hover
      class="mb-0 text-center pcl-tab-prestacao-table"
    >
      <template #cell(prestacao_conta)="data">
        <a v-if="data.value && data.item.link_detail_backend"
          :href="data.item.link_detail_backend"
          target="_blank"
          class="small"
          :title="data.value.__str__"
        >{{ formatDateBR(data.value.data_envio) }}</a>
        <span v-else class="small">{{ data.value ? formatDateBR(data.value.data_envio) : '—' }}</span>
      </template>
      <template #cell(detalhamento)="data">
        <span class="small">{{ data.value || '—' }}</span>
      </template>
      <template #cell(situacao)="data">
        <b-badge :variant="situacaoVariant(data.value)">{{ situacaoLabel(data.value) }}</b-badge>
      </template>
    </b-table>
  </div>
</template>

<script>
import { situacaoVariant, situacaoLabel, formatDateBR } from '../utils/pcl-helpers'

export default {
  name: 'pcl-tab-prestacao',
  props: {
    items: {
      type: Array,
      default: null
    },
    registro: {
      type: Object,
      default: null
    }
  },
  data () {
    return {
      localSortBy: 'prestacao_conta',
      localSortDesc: false
    }
  },
  computed: {
    fields () {
      return [
        { key: 'prestacao_conta', label: 'Prestação de Conta', sortable: true },
        { key: 'detalhamento', label: 'Detalhamento' },
        { key: 'situacao', label: 'Situação' }
      ]
    }
  },
  methods: {
    situacaoVariant,
    situacaoLabel,
    formatDateBR
  }
}
</script>

<style scoped>
.pcl-tab-prestacao-table >>> thead th[aria-sort] {
  cursor: pointer;
  position: relative;
  padding-right: 1.5em;
}
.pcl-tab-prestacao-table >>> thead th[aria-sort]::after {
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  font-size: 0.7em;
  position: absolute;
  right: 0.5em;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.4;
  content: '\f0dc';
}
.pcl-tab-prestacao-table >>> thead th[aria-sort="ascending"]::after {
  content: '\f0de';
  opacity: 1;
}
.pcl-tab-prestacao-table >>> thead th[aria-sort="descending"]::after {
  content: '\f0dd';
  opacity: 1;
}
</style>
