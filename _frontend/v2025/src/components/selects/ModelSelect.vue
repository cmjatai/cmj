<template>
  <div>
    <b-form-select v-model="selected" :options="options" :select-size="height"/>
  </div>
</template>

<script setup>

import { ref, watch, computed } from 'vue'

import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const props = defineProps(
  {
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
    },
    choice: {
      type: String,
      required: true
    },
    ordering: {
      type: String,
      required: false,
      default: ''
    },
    getFromCache: {
      type: Boolean,
      required: false,
      default: true
    },
    value: {
      type: [String, Number, null],
      required: false,
      default: null
    }
  }
)

const emit = defineEmits(['change'])

const selected = ref(props.value)
const options = computed(() => [
  { value: null, text: props.label },
  ...Object.values(syncStore.data_cache[`${props.app}_${props.model}`] || {}).map((item) => {
    return {
      value: item.id,
      text: item[props.choice]
    }
  })
])

watch(selected, (nv) => {
  emit('change', nv)
})

watch(() => props.value, (nv) => {
  selected.value = nv
})

</script>

<style lang="scss">

</style>
