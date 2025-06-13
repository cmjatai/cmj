<template>
  <div class="display-message">
    <AlertMessage
      :message="message"
      v-for="message in messageStore.getMessages"
      :key="message.id"
      :id="`alert-${message.id}`"
    />
  </div>
</template>

<script setup>
  import { useMessageStore } from '~@/js/stores/MessageStore';
  import AlertMessage from './AlertMessage.vue';

  const messageStore = useMessageStore()
</script>

<style scoped>
  .display-message {
    position: fixed;
    bottom: 0;
    right: 0;
    z-index: 1000;
    padding: 1em 2em;
  }
</style>
