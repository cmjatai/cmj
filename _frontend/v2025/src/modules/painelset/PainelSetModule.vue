<template>
  <div class="painelset-module">
    <div class="inner-painelset">
      <router-view />
    </div>
  </div>
</template>
<script setup>
</script>
<style lang="scss" scoped>
  .painelset-module {
    position: absolute;
    top: 30px;
    bottom: 30px;
    left: 30px;
    right: 30px;
    display: flex;
    .inner-painelset {
      position: relative;
    }
  }
</style>
