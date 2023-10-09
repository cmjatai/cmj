<template>
  <div>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'arq-layout',
  methods: {
  },
  mounted: function () {
    this.removeAside()
  }
}
</script>
