<template>
  <div :class="['draft-midia', 'py-3',]" :id="`dm${elemento.id}`">
    <img :src="elemento.arquivo"/>
    <span v-html="elemento.sequencia"></span>
  </div>
</template>

<script>
export default {
  name: 'draft-midia',
  props: ['elemento']
}
</script>

<style lang="scss">
</style>
