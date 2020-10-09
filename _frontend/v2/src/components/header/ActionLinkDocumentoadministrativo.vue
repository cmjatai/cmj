<template>
  <div>
    <div
      v-for="(item, key) in values"
      :key="key">{{item.__str__}}
      <br>
            <i><small>{{item.assunto}}</small></i><br><br>
</div>

  </div>
</template>
<script>
import ActionLink from './ActionLink'
export default {

  name: 'action-link-documentoadministrativo',
  props: ['app', 'model', 'params'],
  extends: {
    ...ActionLink
  },
  methods: {
  }
}
</script>
