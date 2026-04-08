<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted small py-3 text-center">
      Nenhum empenho vinculado.
    </div>
    <template v-else>
      <div class="row px-3 pt-2">
        <div class="col-sm-3 text-center">
          <small class="text-muted d-block">Total Empenhado</small>
          <strong class="text-primary">R$ {{ totalEmpenhado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
        </div>
        <div class="col-sm-3 text-center">
          <small class="text-muted d-block">Total Liquidado</small>
          <strong class="text-info">R$ {{ totalLiquidado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
        </div>
        <div class="col-sm-3 text-center">
          <small class="text-muted d-block">Total Pago</small>
          <strong class="text-success">R$ {{ totalPago.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
        </div>
        <div class="col-sm-3 text-center">
          <small class="text-muted d-block">Total Anulado</small>
          <strong class="text-danger">R$ {{ totalAnulado.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
        </div>
      </div>
      <div
        v-for="(item, idx) in items"
        :key="item.id || idx"
        :class="['hover', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div
          class="d-flex justify-content-between align-items-start p-3 cursor-pointer"
          @click="openModal(item)"
          role="button"
        >
          <div>
            <small class="font-weight-bold">
              <i class="fas fa-file-invoice-dollar mr-1 text-primary"></i>
              Empenho {{ item.empenho.codigo }}
            </small>
            <small class="badge zoom08 badge-warning ml-2" v-if="item.empenho.total_registros > 1">Refere-se a várias emendas e/ou ajustes</small>
            <br>
            <small class="text-muted">
              <strong>Fornecedor:</strong> {{ item.empenho.nome }}
              <span v-if="item.empenho.cpfcnpj"> ({{ item.empenho.cpfcnpj }})</span>
            </small>
            <br>
            <small class="text-muted">
              <strong>Data:</strong> {{ formatDate(item.empenho.data) }}
              <span v-if="item.empenho.modalidade" class="ml-2">
                <strong>Modalidade:</strong> {{ item.empenho.modalidade }}
              </span>
            </small>
            <small v-if="item.empenho.historico" class="text-muted d-block mt-1">
              <strong>Histórico:</strong> {{ item.empenho.historico }}
            </small>
          </div>
          <div class="text-right ml-2 text-nowrap">
            <h3 class="font-weight-bold text-success mb-0">
              R$ {{ formatCurrency(item.empenho.valor_empenhado) }}
            </h3>
            <small class="text-muted" v-if="parseFloat(item.empenho.valor_pago_bruto) > 0">
              Pago: R$ {{ formatCurrency(item.empenho.valor_pago_bruto) }}
            </small>
          </div>
        </div>
      </div>
    </template>

    <!-- Modal de Detalhes do Empenho -->
    <div v-if="showModal" class="empenho-modal-overlay" @click.self="showModal = false">
      <div class="empenho-modal-dialog">
        <div class="empenho-modal-header">
          <h5 class="mb-0">{{ modalTitle }}</h5>
          <button type="button" class="close ml-auto" @click="showModal = false">
            <span>&times;</span>
          </button>
        </div>
        <div class="empenho-modal-body" v-if="selectedEmpenho">
          <!-- Valores -->
          <div class="row mb-3">
            <div class="col-sm-3 text-center">
              <div class="border rounded p-2">
                <small class="text-muted d-block">Empenhado</small>
                <strong class="text-primary">R$ {{ formatCurrency(selectedEmpenho.valor_empenhado) }}</strong>
              </div>
            </div>
            <div class="col-sm-3 text-center">
              <div class="border rounded p-2">
                <small class="text-muted d-block">Liquidado</small>
                <strong class="text-info">R$ {{ formatCurrency(selectedEmpenho.valor_liquidado) }}</strong>
              </div>
            </div>
            <div class="col-sm-3 text-center">
              <div class="border rounded p-2">
                <small class="text-muted d-block">Pago</small>
                <strong class="text-success">R$ {{ formatCurrency(selectedEmpenho.valor_pago_bruto) }}</strong>
              </div>
            </div>
            <div class="col-sm-3 text-center">
              <div class="border rounded p-2">
                <small class="text-muted d-block">Anulado</small>
                <strong class="text-danger">R$ {{ formatCurrency(selectedEmpenho.valor_anulado) }}</strong>
              </div>
            </div>
          </div>

          <!-- Dados do scrap -->
          <template v-if="scrapValues">
            <table class="table table-sm table-bordered">
              <tbody>
                <tr v-for="(value, key) in scrapValues" :key="key">
                  <td class="font-weight-bold text-muted bg-light" style="width: 30%">
                    {{ cleanKey(key) }}
                  </td>
                  <td v-if="key === 'Código:'">
                    <a
                      class="font-weight-bold"
                      :href="selectedEmpenho.link_detail_backend" target="_blank" rel="noopener">
                      {{ value }}
                    </a>
                  </td>
                  <td v-else>
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </table>
          </template>

          <!-- Histórico -->
          <div v-if="selectedEmpenho.historico" class="mt-3">
            <h6 class="font-weight-bold">Histórico</h6>
            <p class="small text-muted bg-light p-2 rounded">
              {{ selectedEmpenho.historico }}
            </p>
          </div>
        </div>
        <div class="empenho-modal-footer">
          <button class="btn btn-secondary btn-sm" @click="showModal = false">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'pcl-tab-empenhos',
  props: {
    items: {
      type: Array,
      default: null
    }
  },
  data () {
    return {
      showModal: false,
      selectedItem: null
    }
  },
  computed: {
    totalEmpenhado () {
      if (!this.items) return 0
      return this.items.reduce((t, i) => t + parseFloat(i.empenho.valor_empenhado || 0), 0)
    },
    totalLiquidado () {
      if (!this.items) return 0
      return this.items.reduce((t, i) => t + parseFloat(i.empenho.valor_liquidado || 0), 0)
    },
    totalPago () {
      if (!this.items) return 0
      return this.items.reduce((t, i) => t + parseFloat(i.empenho.valor_pago_bruto || 0), 0)
    },
    totalAnulado () {
      if (!this.items) return 0
      return this.items.reduce((t, i) => t + parseFloat(i.empenho.valor_anulado || 0), 0)
    },
    selectedEmpenho () {
      return this.selectedItem ? this.selectedItem.empenho : null
    },
    modalTitle () {
      if (!this.selectedEmpenho) return 'Detalhes do Empenho'
      return `Empenho ${this.selectedEmpenho.codigo} - ${this.selectedEmpenho.nome}`
    },
    scrapValues () {
      if (!this.selectedEmpenho) return null
      const md = this.selectedEmpenho.metadata
      if (md && md.scrap && md.scrap.values) {
        return md.scrap.values
      }
      return null
    }
  },
  methods: {
    openModal (item) {
      this.selectedItem = item
      this.showModal = true
    },
    formatDate (dateStr) {
      if (!dateStr) return ''
      const parts = dateStr.split('-')
      if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`
      }
      return dateStr
    },
    formatCurrency (value) {
      const num = parseFloat(value)
      if (isNaN(num)) return '0,00'
      return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    cleanKey (key) {
      return key.replace(/:+$/, '')
    }
  }
}
</script>

<style lang="scss" scoped>
.cursor-pointer {
  cursor: pointer;
}
.empenho-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.empenho-modal-dialog {
  background: #fff;
  border-radius: 0.3rem;
  width: 90%;
  max-width: 800px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.3);
}
.empenho-modal-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #dee2e6;

  .close {
    background: none;
    border: none;
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
  }
}
.empenho-modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex: 1;

  .table td {
    font-size: 0.85rem;
    vertical-align: middle;
  }
}
.empenho-modal-footer {
  padding: 0.5rem 1rem;
  border-top: 1px solid #dee2e6;
  text-align: right;
}
</style>
