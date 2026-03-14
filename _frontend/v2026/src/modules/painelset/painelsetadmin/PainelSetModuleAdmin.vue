<template>
  <div class="painelset-module-admin online-module">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'painelset-module-admin',
  data () {
    return {
    }
  },
  mounted: function () {
    const t = this
    t.setSideleftVisivel(true)
    t.setSiderightVisivel(false)
    t.$nextTick(() => {
      t.registerModels({
        app: 'painelset',
        models: ['evento', 'cronometro', 'individuo']
      })
    })
  }
}
</script>

<style lang="scss">
.painelset-module-admin {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  user-select: none;
}
</style>
