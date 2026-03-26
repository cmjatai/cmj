<template>
  <CronometroBase v-bind="$attrs" />
</template>
<script setup>
import CronometroBase from './CronometroBase.vue'

defineOptions({ name: 'cronometro-global', inheritAttrs: false })
</script>
