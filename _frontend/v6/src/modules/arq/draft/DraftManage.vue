<template>
  <div class="draft-manage container-fluid py-3">
    <div class="row">
      <div class="col-3 d-flex">
        <div class="d-flex flex-column w-100">
          <div class="d-flex">
            <div>
              <button
                type="button"
                class="btn btn-primary"
                title="Novo Draft"
                @click="clickAdd"
              >
                +
              </button>
            </div>
            <h1 class="ms-2">
              Draft
            </h1>
          </div>
          <ModelSelect
            @change="handleDraftChange"
            class="form-opacity d-flex w-100"
            app="arq"
            model="draft"
            choice="descricao"
            label="Selecione um Draft"
            ordering="descricao"
            :height="8"
          />
          <div
            v-if="draftselected"
            class="d-flex flex-column"
          >
            <span>Título do Draft:
              <small><em>(edição do draft selecionado acima)</em></small>
            </span>
            <BFormInput
              v-model="draftselected.descricao"
              @change="val => changeDescricao(draftselected.descricao)"
            />
          </div>
          <div class="drop-area">
            <DropZone
              :pk="draftselected.id"
              :multiple="true"
              @uploaded="uploadedFiles"
              v-if="draftselected"
            />
          </div>
        </div>
      </div>
      <div class="col-9 container-manage-list">
        <div v-show="draftselected">
          <DraftManageList
            :draftselected="draftselected"
            @reload-drafts="reloadDrafts"
            ref="listdraftRef"
          />
        </div>
        <DraftHelp />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Resources from '~@/utils/resources'
import { useSyncStore } from '~@/stores/SyncStore'
import ModelSelect from '~@/components/selects/ModelSelect.vue'
import DropZone from '~@/components/utils/DropZone.vue'
import DraftManageList from './DraftManageList.vue'
import DraftHelp from './DraftHelp.vue'

const syncStore = useSyncStore()

const draftselected = ref(null)
const listdraftRef = ref(null)

async function fetchDrafts () {
  await syncStore.fetchSync({
    app: 'arq',
    model: 'draft',
    params: { o: 'descricao', get_all: 'True' }
  })
}

function handleDraftChange (id) {
  if (id === null) {
    draftselected.value = null
    return
  }
  const cache = syncStore.data_cache['arq_draft'] || {}
  draftselected.value = cache[id] ? { ...cache[id] } : null
}

async function reloadDrafts () {
  draftselected.value = null
  syncStore.data_cache['arq_draft'] = {}
  await fetchDrafts()
}

async function clickAdd () {
  try {
    await Resources.Utils.postModel({
      app: 'arq',
      model: 'draft',
      form: { descricao: `New Draft ${(new Date()).toLocaleString()}` }
    })
    syncStore.data_cache['arq_draft'] = {}
    await fetchDrafts()
  } catch (error) {
    console.debug(error)
  }
}

function uploadedFiles (response) {
  if (response.status === 200) {
    listdraftRef.value?.fetchMidias(draftselected.value, 1)
  }
}

async function changeDescricao (event) {
  await Resources.Utils.patchModel({
    app: 'arq',
    model: 'draft',
    id: draftselected.value.id,
    form: { descricao: event }
  })
  syncStore.data_cache['arq_draft'] = {}
  await fetchDrafts()
}

onMounted(() => {
  fetchDrafts()
})
</script>

<style lang="scss">
.draft-manage {
  min-height: 100vh;
  .flex-column {
    gap: 0.5rem;
  }
  .drop-area {
    position: relative;
    flex-grow: 2;
    .drop_files {
      height: 100%;
      label {
        position: sticky;
        padding: 15vh 0;
      }
    }
  }
  .container-manage-list {
    padding-left: 0;
  }
}

.btn-group-vertical {
  align-content: center;
}
</style>
