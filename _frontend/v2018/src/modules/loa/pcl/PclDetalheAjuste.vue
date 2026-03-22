<template>
  <div class="pcl-detalhe-ajuste">
    <div class="emenda-card card border-0 shadow-sm mb-3">

      <!-- ===== CABEÇALHO ===== -->
      <div class="card-header bg-white border-bottom-0 pb-0">
        <div class="d-flex align-items-start flex-wrap">
          <!-- Título e badges -->
          <div class="flex-grow-1">
            <h4 class="mb-1 font-weight-bold">
              <a :href="registro.link_detail_backend" target="_blank">
                {{ registro.descricao || 'Registro de Ajuste' }}
                <i class="fas fa-external-link-alt fa-sm ml-1 text-muted"></i>
              </a>
            </h4>
            <div class="mb-2">
              <span class="badge mr-1 badge-warning">Registro de Ajuste</span>
              <span
                :class="['badge', 'badge-' + situacaoVariant(registro.fase_prestacao_contas)]"
              >{{ situacaoLabel(registro.fase_prestacao_contas) }}</span>
            </div>
          </div>
        </div>
      </div>

      <hr class="my-0">

      <!-- ===== DADOS PRINCIPAIS ===== -->
      <div class="card-body pt-2 pb-2">
        <div class="row">
          <div class="col-md-12">
            <small class="d-block text-muted" v-if="registro.unidade">
              <strong>Unidade Orçamentária:</strong> {{ registro.unidade.__str__ }}
            </small>
            <small class="d-block text-muted" v-if="emendasLoaFormatadas">
              <strong>Emendas vinculadas:</strong> {{ emendasLoaFormatadas }}
            </small>
          </div>
        </div>

        <!-- Descrição -->
        <div class="mt-2 p-2 bg-light rounded border" v-if="registro.descricao">
          <small class="text-muted">
            <strong>Descrição:</strong>
            {{ registro.descricao }}
          </small>
        </div>
      </div>

      <!-- ===== ABAS ===== -->
      <div class="bg-white p-0 mt-2" v-if="prestacaoItems && prestacaoItems.length">
        <b-tabs
          nav-class="nav-fill emenda-tabs"
          content-class="p-0"
          small
        >
          <b-tab active>
            <template #title>
              Prestação de Contas
              <b-badge
                variant="secondary"
                pill
                class="ml-1"
              >{{ prestacaoItems.length }}</b-badge>
            </template>
            <pcl-tab-prestacao :items="prestacaoItems" :registro="registro" />
          </b-tab>
        </b-tabs>
      </div>

    </div>
  </div>
</template>

<script>
import {
  faseVariant,
  faseLabel,
  situacaoLabel,
  situacaoVariant
} from './utils/pcl-helpers'
import PclTabPrestacao from './tabs/PclTabPrestacao.vue'

export default {
  name: 'pcl-detalhe-ajuste',
  components: {
    PclTabPrestacao
  },
  props: {
    registro: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
      prestacaoItems: null,
      visible: false
    }
  },
  watch: {
    registro: {
      immediate: true,
      handler (reg) {
        if (!reg || !this.visible) return
        this.fetchTabData(reg)
      }
    },
    visible (val) {
      if (val && this.registro) {
        this.fetchTabData(this.registro)
      }
    }
  },
  mounted () {
    this._observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        this.visible = true
        this._observer.disconnect()
      }
    }, { rootMargin: '200px' })
    this._observer.observe(this.$el)
  },
  beforeDestroy () {
    if (this._observer) {
      this._observer.disconnect()
    }
  },
  computed: {
    emendasLoaFormatadas () {
      if (!this.registro.emendaloa) return ''
      const lista = Array.isArray(this.registro.emendaloa)
        ? this.registro.emendaloa
        : [this.registro.emendaloa]
      return lista
        .map(e => (e.__str__ || '').split('-')[0].trim())
        .filter(s => s)
        .join(', ')
    }
  },
  methods: {
    faseVariant,
    faseLabel,
    situacaoLabel,
    situacaoVariant,
    fetchTabData (registro) {
      this.prestacaoItems = null

      this.utils
        .fetch({
          app: 'loa',
          model: 'prestacaocontaregistro',
          params: {
            registro_ajuste: registro.id,
            get_all: 'True',
            expand: 'prestacao_conta'
          }
        })
        .then((response) => {
          this.prestacaoItems = response.data
        })
    }
  }
}
</script>

<style lang="scss" scoped>
.pcl-detalhe-ajuste ::v-deep {
  .emenda-card {
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.12) !important;
    }

    .card-header {
      padding: 1rem;
    }

    h4 a {
      color: inherit;
      text-decoration: none;

      &:hover {
        color: #007bff;
        text-decoration: none;
      }
    }
  }

  .nav-tabs {
    padding: 0 0.5rem;

    .nav-link {
      font-size: 0.85rem;
      font-weight: 600;
      color: #555;
      padding: 0.4rem 0.75rem;

      &.active {
        color: #212529;
      }
    }
  }

  .tab-content {
    border-top: none;
  }
}
</style>
