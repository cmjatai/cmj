<template>
  <div class="painelset-module">
    <div class="inner-painelset">
      <router-view />
    </div>
    <div id="widget-editor" />
  </div>
</template>
<script setup>
</script>
<style lang="scss" scoped>
  .painelset-module {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    flex-direction: row;
    gap: 0em;
    * {
      user-select: none;
    }
    .inner-painelset {
      display: flex;
      flex: 1 1 100%;
      flex-direction: column;
    }
    #widget-editor:not(:empty) {
      flex: 0 0 45%;
    }
  }
</style>
