<template>
  <div
    :id="`isc-${item.__label__}-${item.id}`"
    class="item-de-sessa-control"
  >

  </div>
</template>

<script setup>

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  sessao: {
    type: Object,
    required: true
  }
})
</script>

<style lang="scss">
.item-de-sessao-control {

}
</style>
