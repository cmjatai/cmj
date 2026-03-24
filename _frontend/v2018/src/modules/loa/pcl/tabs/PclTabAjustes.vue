<template>
  <div>
    <div v-if="items === null" class="text-center py-2">
      <b-spinner small></b-spinner> Carregando...
    </div>
    <div v-else-if="items.length === 0" class="text-muted small py-3 text-center">
      Nenhum ajuste vinculado a esta emenda.
    </div>
    <template v-else>
      <div
        v-for="(ajuste, idx) in items"
        :key="ajuste.id || idx"
        :class="['hover', { 'border-bottom': idx < items.length - 1 }]"
      >
        <div class="d-flex justify-content-between align-items-start p-3">
          <div>
            <a
              v-if="ajuste.oficio_ajuste_loa && ajuste.oficio_ajuste_loa.link_detail_backend"
              :href="ajuste.link_detail_backend"
              target="_blank"
              rel="noopener"
            >
              <small class="font-weight-bold">
                {{ ajuste.oficio_ajuste_loa ? (ajuste.oficio_ajuste_loa.epigrafe || ajuste.oficio_ajuste_loa.__str__ || 'Ofício') : '' }}
              </small>
            </a>
            <span v-else>
              <small class="font-weight-bold">
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
          <h3 class="font-weight-bold ml-2 text-nowrap text-success">R$ {{ ajuste.str_valor }}</h3>
        </div>
      </div>
    </template>
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
  }
}
</script>
