<template>
  <div>
    <div
      v-if="items === null"
      class="text-center py-2"
    >
      <div
        class="spinner-border spinner-border-sm"
        role="status"
      >
        <span class="visually-hidden">Carregando...</span>
      </div>
      Carregando...
    </div>
    <div
      v-else-if="items.length === 0"
      class="text-muted small py-3 text-center"
    >
      Nenhum ajuste vinculado a esta emenda.
    </div>
    <template v-else>
      <div class="d-flex justify-content-end align-items-center px-3 pt-2">
        <h3 class="mb-0 me-2 fst-italic border-bottom">
          Total dos Ajustes:
        </h3>
        <h3 class="fw-bold mb-0 text-primary border-bottom">
          R$ {{ totalValor }}
        </h3>
      </div>
      <div
        v-for="(ajuste, idx) in items"
        :key="ajuste.id || idx"
        :class="['pcl-tab-item', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-start p-3">
          <div>
            <a
              v-if="ajuste.oficio_ajuste_loa && ajuste.oficio_ajuste_loa.link_detail_backend"
              :href="ajuste.link_detail_backend"
              target="_blank"
              rel="noopener"
            >
              <small class="fw-bold">
                {{ ajuste.oficio_ajuste_loa ? (ajuste.oficio_ajuste_loa.epigrafe || ajuste.oficio_ajuste_loa.__str__ || 'Ofício') : '' }}
              </small>
            </a>
            <span v-else>
              <small class="fw-bold">
                {{ ajuste.oficio_ajuste_loa ? (ajuste.oficio_ajuste_loa.__str__ || 'Ofício') : '' }}
              </small>
            </span>
            <br>
            <template v-if="ajuste.unidade">
              <small class="text-muted"><strong>Unidade:</strong> {{ ajuste.unidade.__str__ || ajuste.unidade }}</small>
              <br>
            </template>
            <small class="text-muted">{{ ajuste.descricao }}</small>
          </div>
          <h3 class="fw-bold ms-2 text-nowrap text-success">
            R$ {{ ajuste.str_valor }}
          </h3>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatCurrency } from '../utils/pcl-helpers'

const props = defineProps({
  items: { type: Array, default: null }
})

const totalValor = computed(() => {
  if (!props.items) return '0,00'
  const total = props.items.reduce((sum, ajuste) => sum + parseFloat(ajuste.valor || 0), 0)
  return formatCurrency(total)
})
</script>
