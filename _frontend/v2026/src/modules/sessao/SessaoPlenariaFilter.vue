<template>
  <div class="form-sessao-list"> 
    <year-exists-in-model-select
      @change="value => form_filter.year=value"
      class="form-opacity"
      app="sessao"
      model="sessaoplenaria"
      label="Filtre por Ano"
    />
    <month-select
      @change="value => form_filter.month=value"
      class="form-opacity"
    />
    <model-select
      @change="value => form_filter.tipo=value"
      class="form-opacity"
      app="sessao"
      model="tiposessaoplenaria"
      label="Filtre por Tipo de Sessão"
      choice="nome"
      ordering="nome"
      :get-from-cache="true"
    />

    <pagination
      :pagination="pagination"
      @next-page="nextPage"
      @previous-page="previousPage"
      @current-page="currentPage"
    />
  </div>
</template>
<script setup>
import { ref, watch } from 'vue'

import YearExistsInModelSelect from '~@/components/selects/YearExistsInModelSelect'
import Pagination from '~@/components/atoms/Pagination'
import MonthSelect from '~@/components/selects/MonthSelect'
import ModelSelect from '~@/components/selects/ModelSelect'

const props = defineProps({
  pagination: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['changeFilter', 'currentPage', 'nextPage', 'previousPage'])

const form_filter = ref({
  year: null,
  month: null,
  tipo: null
})

watch(() => form_filter.value.year, (nv) => {
  emit('changeFilter', form_filter.value)
})

watch(() => form_filter.value.month, (nv) => {
  emit('changeFilter', form_filter.value)
})

watch(() => form_filter.value.tipo, (nv) => {
  emit('changeFilter', form_filter.value)
})

const currentPage = (value) => {
  emit('currentPage', value)
}

const nextPage = () => {
  emit('nextPage')
}

const previousPage = () => {
  emit('previousPage')
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
  grid-column-gap: 1em;
  padding: 1em 1em 0 1em;
  .form-opacity {
    opacity: 0.7;
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
    grid-row-gap: 1em;
    .widget-pagination {
      grid-column-start: 1;
      grid-column-end: 4;
    }
  }
}
@media screen and (max-width: 480px) {
  .form-sessao-list {
    padding: 0.5em 0.5em 0.25em 0.5em;
    grid-row-gap: 0.5em;
    grid-column-gap: 0.5em;
    select {
      font-size: 80%;
    }

  }
}
</style>
