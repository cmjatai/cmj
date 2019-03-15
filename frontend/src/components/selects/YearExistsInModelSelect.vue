<template>
  <div>
    <b-form-select v-model="selected" :options="options"/>
  </div>
</template>

<script>

import Resources from '@/resources'

export default {
  /**
   * Componente que cria select para qualquer model do Sapl que
   * em sua api rest possua a action years e devolva um array de dict {value, text}
   */
  name: 'year-exists-in-model-select',
  props: ['app', 'model', 'label'],
  data () {
    return {
      utils: Resources.Utils,

      selected: null,
      options: [
        { value: null, text: this.label }
      ]
    }
  },
  watch: {
    selected: function (nv, ov) {
      /**
       * Comunica ao parent que houve alteracão na selecao
       */
      this.$emit('change', nv)
    }
  },
  methods: {
    fetch () {
      /**
       * Busca:
       *   /api/[app]/[model]/years
       *
       */
      this.utils.getYearsChoiceList(this.app, this.model)
        .then((response) => {
          this.options = response.data
          this.options.unshift({ value: null, text: this.label })
        })
        .catch((response) => this.sendMessage(
          { alert: 'danger', message: 'Não foi possível recuperar a lista de anos', time: 5 }))
    }
  },
  created: function () {
    this.fetch()
  }
}
</script>

<style lang="scss">

</style>
