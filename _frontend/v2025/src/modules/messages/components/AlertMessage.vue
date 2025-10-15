<template>
  <div
    class="alert fade show alert-dismissible"
    :class="['alert-' + message.type]"
    role="alert"
  >
    <strong v-if="message.title">{{ message.title }}</strong>
    {{ message.text }}
    <button
      type="button"
      class="btn-close"
      data-bs-dismiss="alert"
      aria-label="Close"
    />
  </div>
</template>
<script setup>
import { defineProps, onMounted } from 'vue'

import { useMessageStore } from '../store/MessageStore'
const messageStore = useMessageStore()

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  id: {
    type: String,
    required: true
  }
})

onMounted(() => {
  if (props.message.timeout) {
    setTimeout(() => {
      messageStore.removeMessage(props.message.id)
    }, props.message.timeout)
  }
})




</script>
