<template>
  <div class="pcl-dashboard">
    <pcl-totalizacao
      v-if="lista.length"
      :lista="lista"
      :parlamentar-selecionado="parlamentarSelecionado"
      :loas-choice="loasChoice"
      :selected-loa-ids="selectedLoaIds"
      :totais-empenhos="totaisEmpenhos"
      class="mt-3"
    />
    <div class="row no-gutters">
      <div class="col-12">
        <pcl-saude
          v-if="lista.length"
          :lista="lista"
          :parlamentar-selecionado="parlamentarSelecionado"
          :loas-choice="loasChoice"
          :selected-loa-ids="selectedLoaIds"
          :totais-empenhos="totaisEmpenhos"
          class="mt-3"
        />
      </div>
    </div>
  </div>
</template>

<script>

import PclTotalizacao from './PclTotalizacao.vue'
import PclSaude from './PclSaude.vue'

export default {
  name: 'pcl-dashboard',
  components: {
    PclTotalizacao,
    PclSaude
  },
  props: {
    lista: { type: Array, default: () => [] },
    parlamentarSelecionado: { type: Object, default: null },
    loasChoice: { type: Array, default: () => [] },
    selectedLoaIds: { type: Array, default: () => [] },
    totaisEmpenhos: { type: Object, default: () => ({}) }
  }
}
</script>
<style lang="scss">
</style>
