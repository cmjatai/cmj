<template>
  <div>
    <img src="@/assets/logo.png" alt="logo" />     
    <HelloWorld msg="Hello Vue 3 + TypeScript + Vite" />
  </div> 
</template> 
<script async setup lang="ts">
  import HelloWorld from '@/components/HelloWorld.vue'
  import { usePageContext } from '@/usePageContext'

  const ctx:any = usePageContext()

  ctx.updateTitle('Título Dinamico')  

</script>
<style>
h1,
a {
  color: green;
}
</style>
