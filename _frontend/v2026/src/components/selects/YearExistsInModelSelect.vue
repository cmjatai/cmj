<template>
  <div>
    <b-form-select v-model="selected" :options="options"/>
  </div>
</template>

<script setup>

import { ref, watch, onMounted } from 'vue'
import Resource from '~@/utils/resources'

const emit = defineEmits(['change'])

const props = defineProps({
  app: {
    type: String,
    required: true
  },
  model: {
    type: String,
    required: true
  },
  label: {
    type: String,
    required: true
  }
})

const selected = ref(null)
const options = ref([
  { value: null, text: 'Selecione um ano' }
])

watch(selected, (nv, ov) => {
  /**
   * Comunica ao parent que houve alteracão na selecao
   */
  emit('change', nv)
})

onMounted(() => {
  Resource.Utils.fetch({
    app: props.app,
    model: props.model,
    action: 'years'
  }).then((response) => {
    options.value = response.data
    options.value.unshift({ value: null, text: props.label })
  })
})

</script>

<style lang="scss">

</style>
