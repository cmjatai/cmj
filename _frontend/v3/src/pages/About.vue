<template>
  <h1>{{ ctx.pageContext.documentProps.title }}</h1>

    <img src="/img/fundo_topo.jpg" alt="logo" />     
</template>

<script setup lang="ts">
  import { usePageContext } from '~/usePageContext'

  const ctx:any = usePageContext()

  ctx.updateTitle('About - Título Dinamico')  

</script>

<style scoped>
h1 {
  color: red;
}
</style>
