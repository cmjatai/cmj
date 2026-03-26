<template>
  <div>
    <b-form-select v-model="selected" :options="options"/>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['change'])

const selected = ref(null)

const options = [
  { value: null, text: 'Filtre por mês...' },
  { value: 1, text: 'Janeiro' },
  { value: 2, text: 'Fevereiro' },
  { value: 3, text: 'Março' },
  { value: 4, text: 'Abril' },
  { value: 5, text: 'Maio' },
  { value: 6, text: 'Junho' },
  { value: 7, text: 'Julho' },
  { value: 8, text: 'Agosto' },
  { value: 9, text: 'Setembro' },
  { value: 10, text: 'Outubro' },
  { value: 11, text: 'Novembro' },
  { value: 12, text: 'Dezembro' }
]

watch(selected, (nv) => {
  emit('change', nv)
})
</script>

<style lang="scss">

</style>
