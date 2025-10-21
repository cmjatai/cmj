<template>
  <div class="display-message">
    <AlertMessage
      v-for="message in messageStore.getMessages"
      :id="`alert-${message.id}`"
      :key="message.id"
      :message="message"
    />
  </div>
</template>

<script setup>
  import { useMessageStore } from '../store/MessageStore'
  import AlertMessage from './AlertMessage'

  const messageStore = useMessageStore()
</script>

<style scoped>
  .display-message {
    position: fixed;
    bottom: 0;
    right: 0;
    z-index: 1000;
  }
</style>
