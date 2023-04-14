<template>
  <div class="draft-manage container-fluid py-3">
    <h1>Draft</h1>
    <div class="row">
      <div class="col-3 d-flex">
        <div class="btn-group-vertical mr-3">
          <button type="button" class="btn btn-primary">+</button>
          <button type="button" class="btn btn-danger">-</button>
        </div>
        <div class="d-flex flex-column w-100">
          <model-select v-on:change="value => draftselected=value"
            class="form-opacity d-flex w-100"
            app="arq"
            model="draft"
            choice="descricao"
            ordering="descricao"
            :height="3"
            ></model-select>
          <div class="pt-2" v-if="draftselected">
            <b-form-input v-model="draftselected.descricao" @change="changeDescricao($event)"></b-form-input>
          </div>
        </div>
      </div>
      <div class="col-9">
        <div class="drop-area">
          <drop-zone :pk="draftselected" :multiple="true" v-on:uploaded="uploadedFiles" v-if="draftselected"/>
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
    uploadedFiles (response) {
      if (response.statusText === 'OK') {
        this.$refs.listdraft.fetchMidias(response.data.id, 1)
      }
    },
    changeDescricao (event) {
      console.log(event)
      let t = this
      t.utils.patchModel('arq', 'draft', this.draftselected.id, {
        descricao: event
      })
        .then((response) => {
          console.log(response)
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
