<template>
  <div class="form-sessao-list">
      <year-exists-in-model-select v-on:change="value => form_filter.year=value" class="form-opacity" app="sessao" model="sessaoplenaria" label="Filtre por Ano"></year-exists-in-model-select>
      <month-select v-on:change="value => form_filter.month=value"  class="form-opacity"></month-select>
      <model-select v-on:change="value => form_filter.tipo=value" class="form-opacity" app="sessao" model="tiposessaoplenaria" label="Filtre por Tipo de Sessão" choice="nome" ordering="nome"></model-select>

      <pagination :pagination="pagination" v-on:nextPage="nextPage" v-on:previousPage="previousPage" v-on:currentPage="currentPage"></pagination>
  </div>
</template>

<script>
import YearExistsInModelSelect from '@/components/selects/YearExistsInModelSelect'
import Pagination from '@/components/Pagination'
import MonthSelect from '@/components/selects/MonthSelect'
import ModelSelect from '@/components/selects/ModelSelect'
export default {
  name: 'form-sessao-list',
  props: ['pagination'],
  components: {
    YearExistsInModelSelect,
    MonthSelect,
    ModelSelect,
    Pagination
  },
  data () {
    return {
      form_filter: {
        year: null,
        month: null,
        tipo: null
      }
    }
  },
  watch: {
    'form_filter.year': function (nv) {
      this.$emit('changeFilter', this.form_filter)
    },
    'form_filter.month': function (nv) {
      this.$emit('changeFilter', this.form_filter)
    },
    'form_filter.tipo': function (nv) {
      this.$emit('changeFilter', this.form_filter)
    }
  },
  methods: {
    currentPage (value) {
      this.$emit('currentPage', value)
    },
    nextPage () {
      this.$emit('nextPage')
    },
    previousPage () {
      this.$emit('previousPage')
    }
  }
}
</script>

<style lang="scss">
.form-opacity {
  opacity: 0.5;
  &:hover {
    opacity: 1;
  }
}
.form-sessao-list {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  grid-column-gap: 15px;
  .form-opacity {
    opacity: 0.4;
  }
  &:hover {
    .form-opacity {
      opacity: 0.6;
      &:hover {
        opacity: 1;
      }
    }
  }
}

@media screen and (max-width: 991px) {
  .form-sessao-list {
    grid-template-columns: 1fr 1fr 1fr;
    grid-row-gap: 15px;
    .widget-pagination {
      grid-column-start: 1;
      grid-column-end: 4;
    }
  }
}
</style>
