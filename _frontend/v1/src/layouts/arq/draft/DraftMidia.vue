<template>
  <div :class="['draft-midia', 'p-2',]" :id="`dm${elemento.id}`">
    <div :class="['inner', elemento.metadata.ocrmypdf.pdfa ? 'border-blue': 'border-red']">
      <div class="inner-action">
        <div class="btn-toolbar" role="toolbar" aria-label="Toolbar with button groups">
          <div class="btn-group-vertical flex-column" role="group" aria-label="First group">
            <a class="btn btn-outline-danger" title="Apagar Mídia" @click="clickDel">
              <i class="fas fa-trash-alt"></i>
            </a>
            <a class="btn btn-outline-primary"
            title="Expandir Páginas" @click="clickExpandir"
            v-show="elemento.metadata.uploadedfile.paginas > 1">
              <i class="fas fa-expand"></i>
            </a>
          </div>
        </div>
      </div>
      <div class="innerimg">
        <a :href="elemento.arquivo" target="_blank">
          <img :src="`${elemento.arquivo}?page=${page}&dpi=48&u=${data}`"/>
        </a>
        <div class="img-actions">
          <div v-show="elemento.metadata.uploadedfile.paginas > 1">
            <b-form-spinbutton id="spinpages" v-model="page" min="1" :max="elemento.metadata.uploadedfile.paginas"></b-form-spinbutton>
          </div>
          <button class="btn btn-sm btn-outline-primary" @click="clickRotate(-90)">
            <i class="fas fa-undo"></i>
          </button>
          <button class="btn btn-sm btn-outline-primary" @click="clickRotate(90)">
            <i class="fas fa-redo"></i>
          </button>
        </div>
      </div>
      <div :class="['innerdesc', ]">
        <strong v-html="elemento.metadata.uploadedfile.name"></strong>
        <small v-show="elemento.metadata.ocrmypdf.pdfa">PDF/A-2 com OCR</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'draft-midia',
  props: ['elemento', 'cols'],
  data () {
    return {
      page: 1,
      data: (new Date()).getTime()
    }
  },
  methods: {
    clickDel () {
      const t = this
      t.utils.deleteModel('arq', 'draftmidia', t.elemento.id)
        .then((response) => {
          t.$emit('redrawDraftMidia')
        }).catch((error) => {
          t.sendMessage(
            { alert: 'danger', message: error.response.data.message, time: 10 }
          )
        })
    },
    clickExpandir () {
      const t = this
      t.utils.getModelAction('arq', 'draftmidia', t.elemento.id, 'expandir')
        .then((response) => {
          t.$emit('redrawDraftMidia')
        }).catch((error) => {
          t.sendMessage(
            { alert: 'danger', message: error.response.data.message, time: 10 }
          )
        })
    },
    clickRotate (angulo) {
      const t = this
      t.utils.getByMetadata({
        action: 'rotate',
        app: 'arq',
        model: 'draftmidia',
        id: t.elemento.id
      }, `page=${t.page}&angulo=${angulo}`)
        .then((response) => {
          this.data = (new Date()).getTime()
        })
        .catch((error) => {
          t.sendMessage(
            { alert: 'danger', message: error.response.data.message, time: 10 }
          )
        })
    }
  }
}
</script>

<style lang="scss">

.draft-midia {
  //max-height: 35vh;
  width: 100%;
  display: flex;
  .inner {
    position: relative;
    padding: 0;
    display: flex;
    width: 100%;
    height: 100%;
    gap: 0;
    overflow: hidden;
    flex-direction: column;
    align-items: center;
    background-color: #fafafa;
    border: 1px solid #ccc;
    &.border-blue, &.border-red, &.border-green {
      z-index: 1;
      &::before {
        content: " ";
        position: absolute;
        display: inline-block;
        width: 20px;
        height: 20px;
        top: 2px;
        left: 2px;
        border-radius: 50%;
        z-index: 1;
      }
    }
    &.border-blue {
      &::before {
        background-color: #0073b7dd;
      }
    }
    &.border-red {
      &::before {
        background-color: #f56954dd;
      }
    }
    &.border-green {
      &::before {
        background-color: #00a65add;
      }
    }
    .inner-action {
      background-color: #fff;
      position: absolute;
      color: #444;
      border-radius: 3px;
      right: 4px;
      top: 4px;
      opacity: 0;
      z-index: 1;
      .btn {
        opacity: 0.4;
        border-width: 0px;
        color: #444;
        border-radius: 50%;
        &:hover {
            opacity: 1;
        }
      }
    }
    .innerimg {
      //height: 100%;
      max-height: 35vh;
      padding: 5px;
      position: relative;
      z-index: 0;
      line-height: 1;
      img {
        border: 1px solid #ccc;
        max-width: 100%;
      }
      .img-actions {
        * {
          line-height: 1;
          height: auto;
        }
        position: absolute;
        bottom: 7px;
        right: 7px;
        opacity: 0;

        display: flex;
        gap: 2px;

        output {
          text-align: center;
        }
        .b-form-spinbutton {
          padding: 2px 1px;
        }
        .btn {
          padding: 2px 4px;
        }
      }
      &:hover {
        .img-actions {
          opacity: 0.8;
        }
      }
    }
    .innerdesc {
      width: 90%;
      text-align: center;
      display: flex;
      flex-direction: column;
    }
    &:hover {
      .inner-action {
        opacity: 1;
      }
    }
  }
  img {
    height: 100%;
    //max-width: 100%;
    //width: auto;
    //height: auto;
  }
}

</style>
