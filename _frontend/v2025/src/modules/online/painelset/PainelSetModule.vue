<template>
  <div class="painelset-module online-module">
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'painelset-module',
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
.painelset-module {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  user-select: none;
}
</style>
