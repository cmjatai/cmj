<template>
  <div class="draftmanagelist py-3">
    <div class="row p-3">
      <div class="col d-flex grade">
        <div class="d-flex grade">
          <b-form-spinbutton id="spincols" v-model="cols" min="1" max="100" inline></b-form-spinbutton>
          <b-form-spinbutton id="spinrows" v-model="rows" min="1" max="100" inline></b-form-spinbutton>
        </div>
        <pagination :pagination="pagination" v-on:nextPage="nextPage" v-on:previousPage="previousPage" v-on:currentPage="currentPage"></pagination>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <draft-midia :elemento="item" :cols="cols" v-for="item, k in draftmidialist_ordered" :key="`dm${k}`"></draft-midia>
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
      cols: 6,
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
    changeMatriz () {
      let dm = document.getElementsByClassName('draft-midia')
      let t = this
      _.each(dm, function (item, idx) {
        item.style.maxWidth = `${100 / t.cols}%`
        item.style.flex = `0 0 ${100 / t.cols}%`
      })
    },
    currentPage (value) {
      console.log('currentPage', value)
      if (value !== null && value >= 0) {
        this.fetchMidias(this.draftselected, value)
      }
    },
    nextPage () {
      this.fetchMidias(this.draftselected, this.pagination.next_page)
    },
    previousPage () {
      this.fetchMidias(this.draftselected, this.pagination.previous_page)
    },
    fetchMidias (draft, page = 1) {
      let _this = this
      if (draft > 0) {
        _this.$set(_this, 'draftmidialist', {})
        _this.$nextTick()
          .then(function () {
            _this.utils.getModelOrderedList('arq', 'draftmidia', 'sequencia', page, `&draft=${draft}&page_size=${_this.rows * _this.cols}`)
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
}
.draft-midia {
  max-height: 25vh;
  img {
    height: 100%;
    width: auto;
  }
}
</style>
