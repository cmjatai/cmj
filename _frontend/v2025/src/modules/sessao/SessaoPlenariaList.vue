<template>
  <div class="sessaoplenaria-list">
    <sessao-plenaria-filter
      :pagination="pagination"
      @change-filter="changeFilter"
      @current-page="currentPage"
      @next-page="nextPage"
      @previous-page="previousPage"
    />
    <div class="sessao-items">
      <sessao-plenaria-item-list
        v-for="sessao in sessoes"
        :key="sessao.id"
        :sessao="sessao"
      />
    </div>
  </div>
</template>

<script setup>
import SessaoPlenariaItemList from './SessaoPlenariaItemList'
import SessaoPlenariaFilter from './SessaoPlenariaFilter'
import { ref, onMounted } from 'vue'

import Resource from '~@/utils/resources'

const pagination = ref({})
const sessoes = ref([])

const changeFilter = (form_filter) => {
  fetchSessaoPlenariaList(1, form_filter)
}
const currentPage = (value) => {
  console.log('currentPage', value)
  fetchSessaoPlenariaList(value)
}

const nextPage = () => {
  if (pagination.value?.current_page < pagination.value?.total_pages) {
    fetchSessaoPlenariaList(pagination.value.current_page + 1)
  }
}

const previousPage = () => {
  if (pagination.value?.current_page > 1) {
    fetchSessaoPlenariaList(pagination.value.current_page - 1)
  }
}
const fetchSessaoPlenariaList = async (page = 1, form_filter = {}) => {
  const params = {
    o: '-data_inicio,-hora_inicio,id',
    page: page,
    page_size: 10,
    year: form_filter.year || '',
    month: form_filter.month || '',
    tipo: form_filter.tipo || '',
    expand: 'tipo;legislatura;sessao_legislativa'
  }

  Resource
    .Utils
    .fetch({
      app: 'sessao',
      model: 'sessaoplenaria',
      params
    })
    .then(response => {
      if (response && response.data.results) {
        pagination.value = response.data.pagination || {}
        sessoes.value = response.data.results || []
      }
    })
    .catch(() => {
      // Handle error
    })
}

onMounted(() => {
  fetchSessaoPlenariaList(1)
})
</script>

<style lang="scss">
.sessaoplenaria-list {
  .sessao-items {
    margin-top: 1em;
  }
}
</style>
