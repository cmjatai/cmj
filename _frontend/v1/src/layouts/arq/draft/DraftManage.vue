<template>
  <div class="draft-manage container-fluid py-3">
    <h1>Draft</h1>
    <div class="row">
      <div class="col-3 d-flex">
        <div class="btn-group-vertical mr-3">
          <button type="button" class="btn btn-primary" @click="clickAdd">+</button>
          <button type="button" class="btn btn-danger" @click="clickDel" :disabled="draftselected === null">-</button>
        </div>
        <div class="d-flex flex-column w-100">
          <model-select @change="value => draftselected=value"
            class="form-opacity d-flex w-100"
            app="arq"
            model="draft"
            choice="descricao"
            ordering="descricao"
            ref="draftSelect"
            :height="3"
            ></model-select>
          <div class="pt-2" v-if="draftselected">
            <b-form-input v-model="draftselected.descricao" @change="changeDescricao($event)"></b-form-input>
          </div>
        </div>
      </div>
      <div class="col-9">
        <div class="drop-area">
          <drop-zone :pk="draftselected.id" :multiple="true" v-on:uploaded="uploadedFiles" v-if="draftselected"/>
        </div>
      </div>
    </div>
    <div v-show="draftselected">
      <draft-manage-list :draftselected="draftselected" ref="listdraft"></draft-manage-list>
    </div>
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'
import DropZone from '@/components/utils/DropZone.vue'
import DraftManageList from './DraftManageList.vue'

export default {
  name: 'draft-manage',
  components: {
    DropZone,
    ModelSelect,
    DraftManageList
  },
  data () {
    return {
      draftselected: null
    }
  },
  methods: {
    clickDel () {
      const t = this
      this.utils.deleteModel('arq', 'draft', this.draftselected.id
      ).then((response) => {
        t.draftselected = null
        t.$refs.draftSelect.fetchModel()
      }).catch((error) => {
        t.sendMessage(
          { alert: 'danger', message: error.response.data.message, time: 10 }
        )
      })
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
  }
}
</script>

<style lang="scss">
@import "~@/scss/variables";
.draft-manage {
  min-height: 100vh;
}

.btn-group-vertical {
  align-content: center;
}
</style>
