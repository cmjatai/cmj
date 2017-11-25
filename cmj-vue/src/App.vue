<template>
  <div id="app">
    <loading v-bind:loading="getLoader"></loading>
    <router-view class="view"></router-view>
  </div>
</template>

<script>

import { mapGetters } from 'vuex';

export default {
  name: 'app',
  computed: {
    ...mapGetters({
      getLoader: 'getLoader',
    }),
  },
};
</script>

<style>
</style>
