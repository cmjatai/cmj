<template>
  <h1>{{ ctx.pageContext.documentProps.title }}</h1>
</template>

<script setup lang="ts">
  import { usePageContext } from '../../app/usePageContext'

  const ctx:any = usePageContext()

  ctx.updateTitle('About - Título Dinamico')  

</script>

<style scoped>
h1 {
  color: red;
}
</style>
