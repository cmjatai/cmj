<template>
  <div :class="['draft-midia', `col-${col}`, 'py-3']" :id="`dm${elemento.id}`">
    <img class="w-100" :src="elemento.arquivo"/>
    <span v-html="elemento.sequencia"></span>
  </div>
</template>

<script>
export default {
  name: 'draft-midia',
  props: ['elemento', 'col']
}
</script>

<style lang="scss">
.draft-midia {
}
</style>
