<template>
  <div>
    <router-view></router-view>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // document.querySelector('aside')?.remove()
})
</script>
