<template>
  <div class="painelset-detail">
    <div v-if="$route.name === 'painelset_detail_link'" class="painelset-detail-header">
      Detalhes do Painel Setting
    </div>
    <router-view></router-view>
  </div>
</template>

<script>

export default {
  name: 'painelset-detail',
  data () {
    return {
    }
  },
  mounted: function () {
  },
  methods: {
  }
}
</script>

<style lang="scss">
</style>
