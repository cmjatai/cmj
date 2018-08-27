<template lang="html">
  <div class="drop_files" :id="'drop_file'+elemento.id" v-on:drop="drop_handler" v-on:dragover="dragover_handler" v-on:dragend="dragend_handler">
    <label class="drop_zone" :for="'input_file'+elemento.id">
      <span class="inner">
        Arraste suas imagens e solte aqui,<br>
        <small>ou clique para selecionar</small>
      </span>
      <input :multiple="multiple ? 'multiple': null" type="file" name="file" :id="'input_file'+elemento.id" @change="selectFiles"/>
    </label>
    <div v-if="elemento.has_midia" class="view">
      <img :src="src_local">
    </div>
  </div>
</template>

<script>
export default {
  name: 'drop-zone',
  props: ['elemento', 'src', 'multiple', 'resource'],
  data () {
    return {
      src_local: this.src
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
      this.sendFiles(files)
    },
    sendFiles (files) {
      let form = new FormData()
      for (var i = 0; i < files.length; i++) {
        form.append('files', files[i])
      }
      let t = this
      t.resource.uploadFiles(t.elemento.id, form)
        .then((response) => {
          t.src_local = t.src + '?'+ _.now() // eslint-disable-line
          t.$emit('change')
        })
        .catch((response) => t.danger())
    },
    drop_handler (ev) {
      if (ev === undefined) {
        return
      }
      console.log('Drop')
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
      console.log('dragOver')
      // Prevent default select and drag behavior
      ev.preventDefault()
    },
    dragend_handler (ev) {
      console.log('dragEnd')
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
  min-height: 150px;
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
  border: 3px dashed #cccfcc;
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
