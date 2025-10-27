<template>
  <div :class="['draft-midia', 'p-2',]" :id="`dm${elemento.id}`">
    <div class="inner" @mouseenter="enterInner" @mouseleave="leaveInner">
      <div :class="['inner-status', elemento.metadata.ocrmypdf.pdfa === 99 ? 'border-green': (elemento.metadata.ocrmypdf.pdfa >= 10 ? 'border-yellow': 'border-red')]"
      v-html="elemento.metadata.ocrmypdf.pdfa === 99 ? 'PDF/A-2b': (elemento.metadata.ocrmypdf.pdfa >= 10 ? 'Conversão Agendada': 'Não PDF/A-2b')"></div>
      <div class="inner-action" ref="inneraction">
        <div class="dropleft" ref="dropleft" v-show="elemento.metadata.ocrmypdf.pdfa !== 10">
          <button class="btn btn-sm" type="button" data-toggle="dropdown" aria-expanded="true" ref="btnDropDownActions">
            <i class="fas fa-ellipsis-v"></i>
          </button>
          <div class="dropdown-menu" ref="dropdown">
            <a
            class="dropdown-item"
            title="PDF -> PDF/A-2b - Conversão rápida, pode não ser feita devido a erros no arquivo."
            @click="clickDraftmidiaAction('pdf2pdfa_rapida')">
            PDF -> PDF/A-2b (Conversão Rápida)</a>
            <a
            class="dropdown-item"
            title="PDF -> PDF/A-2b - Conversão básica, pode demorar um pouco mais que a rápida por aplicar correção de possíveis erros no arquivo. Utilize caso a rápida tenha falhado."
            @click="clickDraftmidiaAction('pdf2pdfa_basica')">
            PDF -> PDF/A-2b (Conversão Básica)</a>
            <a
            class="dropdown-item"
            title="PDF -> PDF/A-2b - Conversão forçada, faz OCR e é mais lenta que a básica. (útil para arquivos digitalizados.)"
            @click="clickDraftmidiaAction('pdf2pdfa_forcada')">
            PDF -> PDF/A-2b (Conversão Forçada)</a>
            <a
            class="dropdown-item"
            title="PDF -> PDF/A-2b - Conversão Compacta, faz OCR, converte para preto e branco e aplica alta compactação no arquivo (ultra lenta e útil para arquivos digitalizados)."
            @click="clickDraftmidiaAction('pdf2pdfa_compacta')">
            PDF -> PDF/A-2b (Conversão de Alta Compactação)</a>
            <a class="dropdown-item" title="Gerar um PDF para cada página" @click="clickDraftmidiaAction('decompor')">Decompor <i class="fas fa-expand"></i></a>
            <a class="dropdown-item" title="Apagar Mídia" @click="clickDel">Apagar <i class="fas fa-trash-alt"></i></a>
          </div>
        </div>
      </div>
      <div class="innerimg">
        <a :href="elemento.arquivo" target="_blank">
          <img :src="`${elemento.arquivo}?page=${page}&dpi=48&nocache=${nocache}&u=${data}`" ref="imgView"/>
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
        <small v-html="`${elemento.arquivo_size[1]} MB`"></small>
        <small v-show="elemento.metadata.ocrmypdf.pdfa === 99">PDF/A-2b com OCR</small>
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
      data: (new Date()).getTime(),
      nocache: ''
    }
  },
  watch: {
    elemento (nw, old) {
      const estagio_execucao = this.elemento.metadata.ocrmypdf.pdfa
      if (estagio_execucao >= 10 && estagio_execucao <= 20) {
        this.timeoutUpdate()
      }
    }
  },
  mounted () {
    this.nocache = ''
    const estagio_execucao = this.elemento.metadata.ocrmypdf.pdfa
    if (estagio_execucao >= 10 && estagio_execucao <= 20) {
      this.timeoutUpdate()
    }
  },
  methods: {
    timeoutUpdate () {
      let t = this
      setTimeout(() => {
        t.utils.getModel('arq', 'draftmidia', t.elemento.id)
          .then((response) => {
            const estagio_execucao = response.data.metadata.ocrmypdf.pdfa
            if (estagio_execucao >= 10 && estagio_execucao <= 20) {
              console.debug('timeoutUpdate novamente')
              t.timeoutUpdate()
            } else {
              console.debug('timeoutUpdate Fim')
              t.$emit('updateElement', response.data)
            }
          })
      }, 5000)
    },
    enterInner (ev) {
      const t = this
      const inneraction = t.$refs.inneraction
      const btnDropDownActions = t.$refs.btnDropDownActions
      const rect = ev.currentTarget.getBoundingClientRect()
      inneraction.style.left = `${rect.left + rect.width - btnDropDownActions.offsetWidth - 2}px`
      inneraction.style.top = `${rect.top + 2}px`
    },
    leaveInner (ev) {
      const t = this
      const dropleft = t.$refs.dropleft
      $(dropleft).dropdown('hide')
      // dropleft.classList.remove('show')
    },
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
    clickDraftmidiaAction (action) {
      const t = this
      t.utils.patchModelAction('arq', 'draftmidia', t.elemento.id, action)
        .then((response) => {
          t.data = (new Date()).getTime()
          t.nocache = (new Date()).getTime()
          t.$nextTick(() => {
            t.$refs.imgView.src = `${t.elemento.arquivo}?page=${t.page}&dpi=48&nocache=${t.nocache}&u=${t.data}`
            t.$emit('redrawDraftMidia')
          })
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
      }, `page=${t.page}&angulo=${angulo}`, 'PATCH')
        .then((response) => {
          t.data = (new Date()).getTime()
          // t.$set(t, 'elemento', response.data)
          // console.debug(response)
          t.$emit('updateElement', response.data)
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
    .inner-status {
      position: absolute;
      display: inline-block;
      width: 20px;
      height: 20px;
      top: 1px;
      left: 1px;
      border-radius: 50%;
      font-size: 0;
      z-index: 1;

      &:hover {
        width: auto;
        height: auto;
        border-radius: 0%;
        top: 0px;
        left: 0px;
        padding: 2px 3px;
        color: #fff;
        font-size: 1rem;
        line-height: 1;

      }

      &.border-green, &.border-red, &.border-green, &.border-yellow {
        &::before {
          content: " ";
          z-index: 1;
        }
      }
      &.border-green {
          background-color: #0073b7dd;
      }
      &.border-red {
          background-color: #f56954dd;
      }
      &.border-yellow {
          background-color: #ffd35add;
          color:black;
      }
      &.border-green {
          background-color: #00a65add;
      }
    }
    .inner-action {
      background-color: #fff;
      position: fixed;
      color: #444;
      border-radius: 3px;
      // right: 4px;
      // top: 4px;
      opacity: 0;
      z-index: 1;
      .btn {
        opacity: 0.4;
        border-width: 0px;
        color: #444;
        cursor: pointer;
        //border-radius: 50%;
        &:hover {
            opacity: 1;
        }
      }
      .dropdown-item {
        cursor: pointer;
      }
      .dropdown-menu {
        position: fixed;
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
