<template>
  <div class="pcl-filtros">
    <div class="row">
      <div class="col-auto d-flex align-items-center">
        <FontAwesomeIcon
          icon="filter"
          class="text-secondary"
        />
        <h5>
          <strong class="text-primary">FILTRAR DADOS</strong>
        </h5>
      </div>
    </div>
    <div class="row">
      <div class="col-xl-1 col-md-2 col-4 mb-2 px-1">
        <label>EXERCÍCIO</label>
        <b-form-select
          :model-value="loaSelected"
          v-model="loaSelected"
          @update:model-value="val => updateFilter('loa', val)"
          :options="loasChoice"
          :required="true"
        />
      </div>
      <div class="col-lg col-md-10 col-8 mb-2 px-1">
        <label class="pcl-filtros-label">Pesquisa</label>
        <div class="input-group">
          <input
            ref="searchInput"
            type="search"
            class="form-control"
            placeholder="Filtre por termos nos Ajustes e Emendas"
            :value="modelValue.search"
            @change="event => updateFilter('search', event.target.value)"
          >
          <button
            class="btn btn-secondary"
            @click="searchInput?.blur()"
            title="Pesquisar"
          >
            <FontAwesomeIcon icon="search" />
          </button>
        </div>
      </div>
      <div class="col-lg-2 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Parlamentares</label>
        <b-form-select
          :model-value="modelValue.parlamentar"
          :options="parlamentaresOptions"
          @update:model-value="val => updateFilter('parlamentar', val)"
          :required="false"
        />
      </div>
      <div class="col-lg-3 col-md-4 col-sm-6 mb-2 px-1">
        <label class="pcl-filtros-label">Entidades</label>
        <b-form-select
          :model-value="modelValue.entidade"
          :options="entidadeOptions"
          @update:model-value="val => updateFilter('entidade', val)"
          :required="false"
        />
      </div>
      <div class="col-lg-3 col-md-4 mb-2 px-1">
        <label class="pcl-filtros-label">Unidade Orçamentária</label>
        <b-form-select
          :model-value="modelValue.unidade"
          :options="unidadeOptions"
          @update:model-value="val => updateFilter('unidade', val)"
          :required="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import Resources from '~@/utils/resources'
import { useSyncStore } from '~@/stores/SyncStore'

const syncStore = useSyncStore()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})
const emit = defineEmits(['update:modelValue'])

function updateFilter (key, val) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}

const loaSelected = ref(null)
const searchInput = ref('')
const parlamentaresOptions = ref()
const entidadeOptions = ref()
const unidadeOptions = ref()

const loasChoice = computed(() => {
  const loas = Object.values(syncStore.data_cache?.loa_loa || {}) || []
  return loas.map(l => ({ value: l, text: l.ano })).sort((a, b) => b.text - a.text)
})

const fetchUnidades = async () => {
  Resources.Utils.fetch({
    app: 'loa',
    model: 'unidadeorcamentaria',
    params: {
      page_size: 100,
      loa: loaSelected.value?.id,
      o: 'codigo,especificacao',
      recebe_emenda_impositiva: true,
      get_all: true
    }
  }).then((response) => {
    unidadeOptions.value = response.data.map(
      u => ({ value: u, text: u.__str__ })
    )
    unidadeOptions.value.unshift({ value : null, text: 'Selecione Unidade Orçamentária' })
  })
}

const fetchEntidades = async () => {
  Resources.Utils.fetch({
    app: 'loa',
    model: 'entidade',
    params: {
      page_size: 100,
      loa: loaSelected.value?.id,
      ativo: 'True',
      o: 'nome_fantasia',
      get_all: true
    }
  }).then((response) => {
    entidadeOptions.value = response.data.map(e => ({ value: e, text: e.nome_fantasia }))
    entidadeOptions.value.unshift({ value : null, text: 'Selecione Entidade' })
  })
}

watch(loasChoice, (newVal) => {
  if (!loaSelected.value && newVal.length > 0) {
    loaSelected.value = newVal[0].value
    updateFilter('loa', loaSelected.value)
  }
})

watch(
  () => loaSelected.value,
  (newVal) => {
    if (newVal) {
      let parlamentares = Object.values(syncStore.data_cache?.parlamentares_parlamentar || {}) || []
      parlamentares = parlamentares.filter(p => newVal.parlamentares?.includes(p.id))
      parlamentaresOptions.value = parlamentares.map(p => ({ value: p, text: p.__str__ }))
        .sort((a, b) => a.text.localeCompare(b.text))
      parlamentaresOptions.value.unshift({ value: null, text: 'Selecione Parlamentar' })

      fetchEntidades()
      fetchUnidades()
    }
  }
  // { immediate: true, deep: true }
)

onMounted(async () => {
  syncStore.fetchSync({
    app: 'loa',
    model: 'loa',
    params: {
      page_size: 100,
      ano__gte: new Date().getFullYear() - 5,
      ordering: '-ano',
      expand: 'parlamentares'
    }
  })
})

</script>

<style lang="scss" scoped>
</style>
