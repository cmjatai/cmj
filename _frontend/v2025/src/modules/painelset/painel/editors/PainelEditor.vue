<template>
  <div
    ref="painelsetPainelEditor"
    :key="`painelset-painel-editor-${painelSelected?.id}`"
    class="painelset-painel-editor"
  >
    <form action="" @change="changeForm($event)">
      <fieldset>
        <legend>Configurações do Painel</legend>
        <div class="container">
          <div class="row py-2">
            <div class="col-6">
              <label for="painel-name" class="form-label">Título do Painel</label>
              <input type="text" class="form-control" v-model="painelSelected.name" placeholder="Título do Painel"/>
            </div>
            <div class="col-6">
              <label for="painel-sessao" class="form-label">Sessão Plenária Associada</label>
              <select
                id="painel-sessao"
                name="sessao_plenaria"
                class="form-select"
                v-model="painelSelected.sessao"
              >
                <option :value="null">-- Nenhuma --</option>
                <option
                  v-for="sessao in sessaoList"
                  :key="`sessao-option-${sessao.id}`"
                  :value="sessao.id"
                >
                  {{ sessao.__str__ }} ({{ sessao.data_inicio }} - {{ sessao.data_fim || '' }})
                </option>
              </select>
            </div>
          </div>
          <div class="row py-2">
            <div class="col-6">
              <div id="div_id_config" class="form-group">
                <label for="painel-config" class="form-label">Configurações do Painel (YAML)</label>
                <div>
                  <textarea
                    id="painel-config"
                    name="config"
                    class="form-control"
                    v-model="yamlValues.config"
                    placeholder="Configurações do Painel em YAML"
                    rows="15"
                    @blur="changeYamlValues"
                  />
                </div>
              </div>
            </div>
            <div class="col-6">
              <div id="div_id_styles" class="form-group">
                <label for="painel-styles" class="form-label">Estilos do Painel (YAML)</label>
                <div>
                  <textarea
                    name="styles"
                    id="painel-styles"
                    class="form-control"
                    v-model="yamlValues.styles"
                    rows="15"
                    placeholder="Estilos do Painel em YAML"
                    @blur="changeYamlValues"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="container">
          <div class="row">
            <div class="col-12">
              <div id="div_id_description" class="form-group">
                <label for="id_description" class="form-label">Descrição do Painel</label>
                <div>
                  <textarea
                    id="id_description"
                    name="description"
                    class="form-control"
                    v-model="painelSelected.description"
                    placeholder="Descrição do Painel"
                    rows="5"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="container actions pt-3">
          <div class="row">
            <div class="col-12">
              <div class="btn-group">
                <button
                  class="btn btn-secondary"
                  @click.stop.prevent="closeEditor($event)"
                  title="Fechar Editor do Painel"
                >
                  <FontAwesomeIcon :icon="['fas', 'times']" />
                </button>
                <button
                  class="btn btn-sm btn-primary"
                  @mousedown.stop.prevent="false"
                  @click.stop.prevent="onAddVisaodepainel($event)"
                  title="Adicionar Visão do Painel"
                >
                  <FontAwesomeIcon :icon="'fa-solid fa-plus'" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </fieldset>
    </form>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { useMessageStore } from '~@/modules/messages/store/MessageStore'
import { computed, ref, watch, inject, onMounted } from 'vue'
import YAML from 'js-yaml'

import Resource from '~@/utils/resources'

const painelsetPainelEditor = ref(null)

const syncStore = useSyncStore()
const messageStore = useMessageStore()

const EventBus = inject('EventBus')

const props = defineProps({
  painelId: {
    type: Number,
    default: 0
  },
  painelSelected: {
    type: Number,
    default: 0
  }
})

const painelSelected = computed(() => {
  return syncStore.data_cache.painelset_painel?.[props.painelSelected] || null
})

const yamlConfig = computed(() => {
  if (!painelSelected.value || !painelSelected.value.config) {
    return ''
  }
  return YAML.dump(painelSelected.value.config)
})

const yamlStyles = computed(() => {
  if (!painelSelected.value || !painelSelected.value.styles) {
    return ''
  }
  return YAML.dump({
    component: painelSelected.value.styles.component || {},
    title: painelSelected.value.styles.title || {display: 'flex'},
    inner: painelSelected.value.styles.inner || {}
  })
})

const yamlValues = ref({
  config: yamlConfig.value,
  styles: yamlStyles.value
})

const sessaoList = computed(() => {
  return _.orderBy(syncStore.data_cache?.sessao_sessaoplenaria || [], ['data_inicio'], ['desc'])
})

onMounted(() => {
  syncStore.fetchSync({
    app: 'sessao',
    model: 'sessaoplenaria',
    params: {
      o: '-data_inicio'
    },
    only_first_page: true
  })
})

const changeYamlValues = () => {
  if (!painelSelected.value) {
    return
  }
  try {
    const parsedConfig = yamlValues.value.config ? YAML.load(yamlValues.value.config) : {}
    const parsedStyles = yamlValues.value.styles ? YAML.load(yamlValues.value.styles) : {}
    painelSelected.value.styles = parsedStyles
    painelSelected.value.config = parsedConfig
    yamlValues.value.config = YAML.dump(parsedConfig)
    yamlValues.value.styles = YAML.dump(parsedStyles)
    patchModel({
      config: parsedConfig,
      styles: parsedStyles
    })
  } catch (e) {
    messageStore.addMessage({
      type: 'danger',
      text: `Erro ao atualizar os campos YAML: ${e.message}`,
      timeout: 10000
    })
    console.error('Erro ao atualizar os campos YAML:', e)
    yamlValues.value.config = yamlConfig.value
    yamlValues.value.styles = yamlStyles.value
  }
}

const changeForm = (event) => {
  console.log('PainelEditor.vue: changeForm event:', event)
  const nnv = {...painelSelected.value}
  delete nnv.id

  if (!['styles', 'config'].includes(event.target.name)) {
    patchModel(nnv)
  }
}

const patchModel = async (modelData) => {
  try {
    await Resource.Utils.patchModel({
      app: 'painelset',
      model: 'painel',
      id: painelSelected.value.id,
      form: modelData
    })
    messageStore.addMessage({
      type: 'info',
      text: 'Painel atualizado.',
      timeout: 2000
    })
    console.log('PainelEditor.vue: patchModel updated successfully.')
  } catch (error) {
    messageStore.addMessage({
      type: 'danger',
      text: 'Erro ao salvar as alterações do Painel.',
      timeout: 5000
    })
    console.error('Erro ao salvar as alterações do Painel:', error)
  }
}

watch(
  () => painelSelected.value,
  (newVal) => {
    if (newVal) {
      yamlValues.value.config = yamlConfig.value
      yamlValues.value.styles = yamlStyles.value
    }
  }
)

const closeEditor = (event) => {
  EventBus.emit('painelset:editorarea:close')
  EventBus.emit('painelset:editorarea:resize', 0)
}

const onAddVisaodepainel = (event) => {
  if (!painelSelected.value) {
    return
  }
  const newVisao = {
    painel: painelSelected.value.id,
    name: 'Nova Visão do Painel',
    description: '',
    position: syncStore.data_cache.painelset_visaodepainel
      ? Object.values(syncStore.data_cache.painelset_visaodepainel)
        .filter(w => w.painel === painelSelected.value.id).length + 1
      : 1,
    active: true,
    config: {
    },
    styles: {
      component: {},
      title: {display: 'flex'},
      inner: {}
    }
  }
  Resource.Utils.createModel({
    app: 'painelset',
    model: 'visaodepainel',
    form: newVisao
  })
  .then((response) => {
    messageStore.addMessage({
      type: 'info',
      text: 'Visão do Painel criada com sucesso.',
      timeout: 2000
    })
    syncStore.fetchSync({
      app: 'painelset',
      model: 'visaodepainel',
      params: {
        painel: painelSelected.value.id
      }
    })
  })
  .catch((error) => {
    messageStore.addMessage({
      type: 'danger',
      text: 'Erro ao criar a Visão do Painel.',
      timeout: 5000
    })
    console.error('Erro ao criar a Visão do Painel:', error)
  })
}
</script>

<style lang="scss" scoped>
.painelset-painel-editor {
  * {
    user-select: text !important;
  }
  #painel-config,
  #painel-styles {
    height: 100%;
    font-family: monospace;
  }
  height: 100%;
}
</style>
