<template>
  <div :class="['draft-midia', 'p-2',]" :id="`dm${elemento.id}`">
    <div :class="['inner', elemento.metadata.ocrmypdf.pdfa ? 'border-blue': (elemento.metadata.uploadedfile.content_type === 'application/pdf' ? 'border-red' : 'border-green')]">
      <div class="inner-action">
        <div class="btn-toolbar" role="toolbar" aria-label="Toolbar with button groups">
          <div class="btn-group" role="group" aria-label="First group">
            <a class="btn btn-outline-danger" title="Apagar Mídia"  @click="clickDel">
              <i class="fas fa-trash-alt"></i>
            </a>
          </div>
        </div>
      </div>
      <div class="innerimg">
        <a :href="elemento.arquivo" target="_blank">
          <img :src="`${elemento.arquivo}?page=1&dpi=96`"/>
        </a>
      </div>
      <div :class="['innerdesc', ]">
        <strong v-html="elemento.metadata.uploadedfile.name"></strong><br>
        <small v-show="elemento.metadata.ocrmypdf.pdfa">PDF/A-2 com OCR</small>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'draft-midia',
  props: ['elemento', 'cols'],
  methods: {
    clickDel () {
      const t = this
      t.utils.deleteModel('arq', 'draftmidia', t.elemento.id)
        .then((response) => {
          t.$emit('deletedDraftMidia')
        }).catch((error) => {
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
    gap: 10px;
    overflow: hidden;
    flex-direction: column;
    align-items: center;
    background-color: white;
    border: 1px solid #ccc;
    &.border-blue, &.border-red, &.border-green {
      &::before {
        content: " ";
        position: absolute;
        display: inline-block;
        width: 20px;
        height: 20px;
        top: 2px;
        left: 2px;
        border-radius: 50%;
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
    a {
    }
    .inner-action {
      background-color: white;
      position:absolute;
      color: #444;
      border-radius: 3px;
      right: 7px;
      top: 7px;
      opacity: 0.4;
      .btn {
        border-width: 0px;
        color: #444;
        border-radius: 50%;
        &:hover {
            color: white;
        }
      }
      &:hover {
        opacity: 1;
      }
    }
    .innerimg {
      height: 100%;
      max-height: 35vh;
    }
    .innerdesc {
      width: 90%;
      text-align: center;
    }
    &:hover {
      .innerdesc {
      }
    }
  }
  img {
    height: 100%;
    //max-width: 100%;
    //width: auto;
    //height: auto;
    padding: 10px 3px;
  }
}

</style>
