<template>
  <div>painelset-layout
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'painelset-layout',
  methods: {
  },
  mounted: function () {
    this.removeAside()
  }
}
</script>
