<template>
  <div class="draftmanagelist">
    <div class="row">
      <div class="col d-flex grade">
        <div class="btn-group ">
          <button class="btn" title="Atualizar lista" @click="drawList(0)">
            <i class="fas fa-sync-alt"></i>
          </button>
        </div>
        <div class="d-flex grade">
          <b-form-spinbutton id="spincols" v-model="cols" min="1" max="12" inline></b-form-spinbutton>
          <b-form-spinbutton id="spinrows" v-model="rows" min="1" max="100" inline></b-form-spinbutton>
        </div>
        <pagination :pagination="pagination" v-on:nextPage="nextPage" v-on:previousPage="previousPage" v-on:currentPage="currentPage"></pagination>
        <div v-if="draftselected" class="btn-toolbar" role="toolbar" aria-label="Toolbar with button groups">
          <a class="btn btn-danger" title="Excluir Draft Atual" @click="clickDel" :disabled="draftselected === null">
              <i class="fas fa-trash-alt"></i>
          </a>
          <a class="btn btn-warning text-white ml-2"  @click="clickSupendeConversao" title="Cancela agendamentos de conversão de PDF -> PDF/A-2b">
            <i class="fas fa-stop-circle"></i>
          </a>
          <a class="btn btn-primary ml-2 btn-pdf2pdfa" @click="clickPdf2Pdfa"  title="Iniciar conversão para PDF/A-2b de todos os arquivos do Draft selecionado.">
            <span>
              PDF -><br>PDF/A-2b
            </span>
          </a>
          <a class="btn btn-primary ml-2" :href="`/api/arq/draft/${draftselected.id}/zipfile/`" target="_blank" rel="noopener noreferrer" title="Baixar todos os arquivos individualmente dentro de um arquivo compactado.">
            <i class="fas fa-file-archive"></i>
          </a>
          <a class="btn btn-primary ml-2" @click="clickUnir" title="Unir PDFs do Draft em apenas um PDF">
            <i class="fas fa-layer-group"></i>
          </a>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <draft-midia :elemento="item" :cols="cols" v-for="item, k in draftmidialist_ordered" :key="`dm${k}`" v-on:redrawDraftMidia="drawList(-1)" v-on:updateElement="updateElement"></draft-midia>
      </div>
    </div>
  </div>
</template>

<script>
import DraftMidia from './DraftMidia.vue'
import Pagination from '@/components/Pagination'

export default {
  name: 'draft-manage-list',
  props: ['draftselected'],
  components: {
    DraftMidia,
    Pagination
  },
  data () {
    return {
      pagination: {},
      draftmidialist: {},
      cols: 4,
      rows: 3
    }
  },
  computed: {
    draftmidialist_ordered: {
      get () {
        return _.orderBy(this.draftmidialist, ['sequencia'], ['asc'])
      }
    }
  },
  watch: {
    draftselected (nw, old) {
      this.fetchMidias(nw)
    },
    rows (nw, old) {
      this.fetchMidias(this.draftselected)
    },
    cols (nw, old) {
      this.fetchMidias(this.draftselected)
    }
  },
  mounted () {
    this.changeMatriz()
  },
  methods: {
    clickUnir () {
      const t = this
      t.utils.getModelAction('arq', 'draft', this.draftselected.id, 'unirmidias'
      ).then((response) => {
        this.fetchMidias(this.draftselected)
      }).catch((error) => {
        t.sendMessage(
          { alert: 'danger', message: error.response.data.message, time: 10 }
        )
      })
    },
    clickSupendeConversao () {
      const t = this
      t.utils.getModelAction('arq', 'draft', this.draftselected.id, 'cancela_pdf2pdfa'
      ).then((response) => {
        this.fetchMidias(this.draftselected)
      }).catch((error) => {
        t.sendMessage(
          { alert: 'danger', message: error.response.data.message, time: 10 }
        )
      })
    },
    clickPdf2Pdfa () {
      const t = this
      t.utils.getModelAction('arq', 'draft', this.draftselected.id, 'pdf2pdfa'
      ).then((response) => {
        this.fetchMidias(this.draftselected)
      }).catch((error) => {
        t.sendMessage(
          { alert: 'danger', message: error.response.data.message, time: 10 }
        )
      })
    },
    clickDel () {
      const t = this
      this.utils.deleteModel('arq', 'draft', this.draftselected.id
      ).then((response) => {
        t.$emit('reloadDrafts')
      }).catch((error) => {
        t.sendMessage(
          { alert: 'danger', message: error.response.data.message, time: 10 }
        )
      })
    },
    drawList (value) {
      let l = Object.keys(this.draftmidialist).length
      if (value === -1) {
        this.fetchMidias(this.draftselected, l > 1 ? this.pagination.page : (this.pagination.previous_page || 1))
      } else {
        this.fetchMidias(this.draftselected, l > 0 ? this.pagination.page : (this.pagination.previous_page || 1))
      }
    },
    changeMatriz () {
      let dm = document.getElementsByClassName('draft-midia')
      let t = this
      _.each(dm, function (item, idx) {
        item.style.maxWidth = `${100 / t.cols}%`
        item.style.flex = `0 0 ${100 / t.cols}%`
      })
    },
    currentPage (value) {
      if (value !== null && value >= 0) {
        this.fetchMidias(this.draftselected, value)
      }
    },
    updateElement (el) {
      this.$set(this.draftmidialist, el.id, el)
    },
    nextPage () {
      this.fetchMidias(this.draftselected, this.pagination.next_page)
    },
    previousPage () {
      this.fetchMidias(this.draftselected, this.pagination.previous_page)
    },
    fetchMidias (draft, page = 1) {
      let _this = this
      if (draft !== null && draft.id > 0) {
        _this.$set(_this, 'draftmidialist', {})
        _this.$nextTick()
          .then(function () {
            _this.utils.getModelOrderedList('arq', 'draftmidia', 'sequencia', page, `&draft=${draft.id}&page_size=${_this.rows * _this.cols}`)
              .then((response) => {
                _this.$set(_this, 'pagination', response.data.pagination)
                _.each(response.data.results, function (item, idx) {
                  _this.$set(_this.draftmidialist, item.id, item)
                })
              })
              .then(function () {
                _this.changeMatriz()
              })
              .catch((response) => _this.sendMessage(
                { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 }))
          })
      } else {
        _this.$set(_this, 'draftmidialist', {})
      }
    }
  }
}
</script>

<style lang="scss">
.draftmanagelist {
  .grade {
    gap: 1em;
  }
  .b-form-spinbutton {
    output {
      padding: 0 10px;
    }
  }
  .widget-pagination {
    flex: 1 1 auto;
  }
  .btn-pdf2pdfa {
    font-size: 10px;
    line-height: 1;
    display: flex;
    align-items: center;
    padding: 3px;
  }
}
</style>
