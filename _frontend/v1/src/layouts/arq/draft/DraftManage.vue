<template>
  <div class="draft-manage container-fluid py-3">
    <div class="row">
      <div class="col-3 d-flex">
        <div class="d-flex flex-column w-100">
          <div class="d-flex ">
            <div>
              <button type="button" class="btn btn-primary" title="Novo Draft" @click="clickAdd">+</button>
            </div>
            <h1 class="ml-2">Draft</h1>
          </div>
          <model-select @change="value => draftselected=value"
            class="form-opacity d-flex w-100"
            app="arq"
            model="draft"
            choice="descricao"
            ordering="descricao"
            ref="draftSelect"
            :height="8"
            ></model-select>
          <div v-if="draftselected" class="d-flex">
            <b-form-input v-model="draftselected.descricao" @change="changeDescricao($event)"></b-form-input>
          </div>
          <div class="drop-area">
            <drop-zone :pk="draftselected.id" :multiple="true" v-on:uploaded="uploadedFiles" v-if="draftselected"/>
          </div>
        </div>
      </div>
      <div class="col-9 container-manage-list">
        <div v-show="draftselected">
          <draft-manage-list :draftselected="draftselected" v-on:reloadDrafts="reloadDrafts" ref="listdraft"></draft-manage-list>
        </div>
        <draft-help/>
      </div>
    </div>
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'
import DropZone from '@/components/utils/DropZone.vue'
import DraftManageList from './DraftManageList.vue'
import DraftHelp from './DraftHelp.vue'

export default {
  name: 'draft-manage',
  components: {
    DropZone,
    ModelSelect,
    DraftManageList,
    DraftHelp
  },
  data () {
    return {
      draftselected: null
    }
  },
  methods: {
    reloadDrafts () {
      this.draftselected = null
      this.$refs.draftSelect.fetchModel()
    },
    clickAdd () {
      const t = this
      this.utils.postModel('arq', 'draft', {
        descricao: `New Draft ${(new Date()).toLocaleString()}`
      }).then((response) => {
        t.$refs.draftSelect.fetchModel()
      }).catch((error) => {
        console.log(error)
      })
    },
    uploadedFiles (response) {
      if (response.statusText === 'OK') {
        this.$refs.listdraft.fetchMidias(this.draftselected, 1)
      }
    },
    changeDescricao (event) {
      const t = this
      t.utils.patchModel('arq', 'draft', t.draftselected.id, {
        descricao: event
      })
        .then((response) => {
          t.$refs.draftSelect.fetchModel()
        })
    }
  },
  mounted: function () {
    this.removeAside()
  }
}
</script>

<style lang="scss">
@import "~@/scss/variables";
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
