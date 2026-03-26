<template>
  <nav aria-label="breadcrumb" v-if="parents">
    <ol class="breadcrumb">
      <li class="breadcrumb-item" v-for="(parent, k) in parentsAndMe" :key="`cp-${k}`">
        <router-link :to="{ name: 'arqchildroute', params: { node: k > 0 ? parents[k - 1].id : 'root', nodechild: parent.id } }">
          {{ parent.titulo }}
        </router-link>
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  parents: { type: Array, default: () => [] },
  me: { type: Object, default: null }
})

const parentsAndMe = ref([])

onMounted(() => {
  if (!props.me) {
    parentsAndMe.value = props.parents
  } else {
    parentsAndMe.value = [...props.parents, { id: props.me.id, titulo: props.me.titulo }]
  }
})
</script>

<style lang="scss">
</style>
