<template>
  <div class="individuo-list">
    <individuo-base
      v-for="individuo, index in individuos"
      :key="`individuo-${individuo.id}-${index}`"
      :individuo_id="individuo.id"
      :individuo="individuo"/>
  </div>
</template>
<script>
import IndividuoBase from '../components/individuos/IndividuoBase.vue'
export default {
  name: 'individuo-list',
  props: {
    evento: {
      type: Object,
      required: true
    }
  },
  components: {
    IndividuoBase
  },
  data () {
    return {
      init: false,
      itens: {
        individuo_list: {}
      }
    }
  },
  mounted () {
    console.log('IndividuoList mounted', this.evento)
    const t = this
    t.fetchModelOrderedList('painelset', 'individuo', 'order')
  },
  computed: {
    individuos: function () {
      return _.orderBy(
        this.itens.individuo_list,
        ['order', 'name'],
        ['asc', 'asc']
      )
    }
  },
  methods: {
  }
}
</script>
<style lang="scss">
.individuo-list {
  // border: 1px solid #ccc;
  // border-radius: 4px;
  background: #f9f9f9;
  cursor: pointer;

}
</style>
