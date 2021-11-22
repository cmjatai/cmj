<template>
  <h1>{{ ctx.pageContext.documentProps.title }}</h1>
  <br>
  <div v-for="(item, index) in autores" :key="index">
    {{item.__str__}}
    <br>
    <span v-html="item.nome"></span>
  </div>
</template>

<script setup lang="ts">
import { usePageContext } from '@/usePageContext'
import { onMounted, ref } from 'vue'
import { useStore } from 'vuex'
const store = useStore()
const ctx:any = usePageContext()
ctx.updateTitle('About - Título Dinamico')  

const teste = ref('a')

onMounted(() => {
  console.log('mountou About - composition')
  teste.value = 'montou no setup'
})



</script>

<script lang="ts">
export default {
  computed: {
    autores () {
      return this.store.state.teste.autores
    }
  },
  async serverPrefetch() {
    console.log('serverPrefetch - entrou')
    await this.fetchAutores()

    console.log('serverPrefetch - saiu')
  },
  mounted() {    
    console.log('mountou About - option')
    if (Object.keys(this.autores).length === 0) {
      console.log('mountou About - option - entrou if')

      this.fetchAutores()
    }
  },

  methods: {
    fetchAutores () {
      return this.store.dispatch('teste/fetchAutores')
    }
  }
}
</script>
<style lang="scss" scoped>
div {
  margin: 30px;
}
</style>