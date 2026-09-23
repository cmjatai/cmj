<template>
  <div class="pcl-dashboard">

  </div>
</template>

<script>

/*
import { isEmenda, faseLabel, situacaoLabel } from './utils/pcl-helpers'

const TOP_N = 10

const TIPO_SHORT = {
  0: 'Modificativa',
  10: 'Saúde',
  99: 'Áreas Diversas'
}

const DASH_SITUACAO_PALETTE = [
  '#4e79a7', // azul aço
  '#f28e2b', // laranja
  '#e15759', // vermelho coral
  '#59a14f', // verde
  '#76b7b2', // verde-água
  '#edc948', // amarelo
  '#b07aa1', // roxo
  '#ff9da7', // rosa
  '#9c755f', // marrom
  '#86bcb6', // ciano
  '#8cd17d', // verde claro
  '#d37295', // rosa escuro
  '#499894', // teal
  '#b6992d', // dourado
  '#bab0ac' // cinza
]
*/

export default {
  name: 'pcl-dashboard',
  props: {
    lista: { type: Array, default: () => [] },
    parlamentarSelecionado: { type: Object, default: null }
  }
}
</script>
<style lang="scss">
</style>
