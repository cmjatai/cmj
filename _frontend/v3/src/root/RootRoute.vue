<template>
      <slot></slot>

  <v-app v-if="false">
    <v-main>
      <v-app-bar density="default">
        <v-app-bar-title>Vuetify</v-app-bar-title>
        <v-spacer></v-spacer>
        <v-btn text>Developer</v-btn>
        <v-btn class="mr-3" text>Help</v-btn>
        <v-divider inset vertical></v-divider>
        <v-btn
          class="mr-4 ml-5"
          color="primary"
          plain
        >
        <v-icon left icon="mdi-handshake-outline"></v-icon>
          <span>John Leider</span>
        </v-btn>
      </v-app-bar>

      <router-view/>

        <push></push>
    </v-main>
  </v-app>
</template>
<script>
import Push from './Push.vue'
export default {
  components: {
    Push
  }
}
</script>
<style lang="scss">
</style>
