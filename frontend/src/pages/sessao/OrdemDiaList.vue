<template>
  <div class="ormdemdia-list">
    <div class="inner-list">
      <div class="empty-list" v-if="itens.ordemdia_list.length === 0 && init">
          Não existem Itens na Ordem do Dia com seus critérios de busca!
      </div>
      <div class="empty-list" v-if="!init">
          Carregando listagem...
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ormdemdia-list',
  props: ['sessao'],
  data () {
    return {
      itens: {
        ordemdia_list: []
      },
      init: false,

      app: ['sessao'],
      model: ['ordemdia']

    }
  }

}
</script>

<style lang="scss">

</style>
