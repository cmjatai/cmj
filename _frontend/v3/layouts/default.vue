<template>
  <div>
    <v-app>
      <v-main>
        <Nuxt />
      </v-main>
      <pull-messages></pull-messages>
    </v-app>
  </div>
</template>

<script>
import PullMessages from '~/components/utils/PullMessages.vue'
export default {
  components: {
    PullMessages,
  },
}
</script>

<style>
</style>