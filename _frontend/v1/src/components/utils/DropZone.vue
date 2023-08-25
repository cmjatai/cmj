<template lang="html">
  <div class="drop_files" :id="'drop_file'" v-on:drop="drop_handler" v-on:dragover="dragover_handler" v-on:dragend="dragend_handler">
    <div class="progress" :style="`width: ${progress}`"></div>
    <label class="drop_zone" :for="'input_file'">
      <span class="inner" v-if="multiple">
        Arraste seus arquivos e solte aqui,<br>
        <small>ou clique para selecionar</small>
      </span>
      <span class="inner" v-if="!multiple">
        Arraste seu arquivo e solte aqui,<br>
        <small>ou clique para selecionar</small>
      </span>
      <input :multiple="multiple ? 'multiple': null" type="file" name="file" :id="'input_file'" @change="selectFiles"/>
    </label>
    <div class="view">
      <img :src="src_local" v-if="src">
    </div>
  </div>
</template>

<script>
export default {
  name: 'drop-zone',
  props: ['src', 'multiple', 'pk'],
  data () {
    return {
      src_local: this.src,
      progress: '0%'
    }
  },
  watch: {
    src: function (nv, ov) {
      this.src_local = this.src
    }
  },
  methods: {
    selectFiles (ev) {
      let files = ev.currentTarget.files
      if (files.length === 0) {
        return
      }
      // console.log(files)
      this.sendFiles(files)
    },
    sendFiles (files) {
      let t = this
      let form = new FormData()
      for (var i = 0; i < files.length; i++) {
        form.append('arquivos', files[i])
        form.append('lastmodified', files[i].lastModified)
      }
      t.utils.postModelAction('arq', 'draft', t.pk, 'uploadfiles', form, {
        onUploadProgress: (event) => {
          let _progress = Math.round(
            (event.loaded * 100) / event.total
          )
          this.progress = `${_progress}%`
        }
      })
        .then((response) => {
          this.progress = '0%'

          t.src_local = t.src + '?'+ _.now() // eslint-disable-line
          t.$emit('uploaded', response)
          t.sendMessage({ alert: 'success', message: 'Envio de Arquivos concluído...', time: 5 })
        })
        .catch((response) => t.sendMessage(
          { alert: 'danger', message: 'Não foi possível enviar os arquivos...', time: 5 }))
      /*
      */
    },
    drop_handler (ev) {
      if (ev === undefined) {
        return
      }
      // console.log('Drop')
      ev.preventDefault()

      var dt = ev.dataTransfer

      if (dt.items) {
        let files = Array() // eslint-disable-line
        for (let i = 0; i < dt.items.length; i++) {
          if (dt.items[i].kind === 'file') {
            files.push(dt.items[i].getAsFile())
          }
        }
        this.sendFiles(dt.files)
      } else {
        this.sendFiles(dt.files)
      }
    },
    dragover_handler (ev) {
      // console.log('dragOver')
      // Prevent default select and drag behavior
      ev.preventDefault()
    },
    dragend_handler (ev) {
      // console.log('dragEnd')
      // Remove all of the drag data
      let dt = ev.dataTransfer
      if (dt.items) {
        // Use DataTransferItemList interface to remove the drag data
        for (var i = 0; i < dt.items.length; i++) {
          dt.items.remove(i)
        }
      } else {
        // Use DataTransfer interface to remove the drag data
        ev.dataTransfer.clearData()
      }
    }
  }
}
</script>
<style lang="scss">
.drop_files {
  width:  100%;
  text-align: center;
  background: transparentize(#fff, 0.5);
  position: relative;
  min-height: 120px;
  border: 3px dashed #cccfcc;
  .progress {
    background: #3390fa;
    line-height: 7px;
    height: 7px;
  }
  input {
    visibility: hidden;
    position: fixed;
    top: -100px;
    left: -100px;
    height: 0px;
    width: 0px;
  }
}
.drop_zone {
  cursor: pointer;
  position: absolute;
  line-height: 1;
  margin: 0;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: transparentize(#fff, 0.5);
  opacity: 0.5;
  span {
    color: black;
    small {
      color: #000080;
    }
  }
  &:hover {
    opacity: 1;
  }
}
</style>
