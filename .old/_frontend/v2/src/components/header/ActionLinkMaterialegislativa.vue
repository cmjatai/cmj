<template>
  <div>
    <div v-for="(item, key) in values" :key="key">
      {{item.__str__}}
      <br>
      <i><small>{{item.ementa}}</small></i><br><br>
    </div>

  </div>
</template>
<script>
import ActionLink from './ActionLink'
export default {
  name: 'action-link-materialegislativa',
  props: ['app', 'model', 'params'],
  extends: {
    ...ActionLink
  },
  methods: {
  }
}
</script>
