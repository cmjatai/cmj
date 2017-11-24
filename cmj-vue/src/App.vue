<template>
  <div id="app">
    <loading v-bind:loading="getLoader"></loading>
    <router-view class="view"></router-view>
  </div>
</template>

<script>

import { mapGetters } from 'vuex';
import Loading from './utils-components/Loading.vue';

export default {
  name: 'app',
  computed: {
    ...mapGetters({
      getLoader: 'getLoader',
    }),
  },
  components: {Loading},
};
</script>

<style>
</style>
