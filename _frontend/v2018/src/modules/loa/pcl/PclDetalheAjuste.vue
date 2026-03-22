<template>
  <div class="pcl-detalhe-ajuste">
    <div class="emenda-card card border-0 shadow-sm mb-3">

      <!-- ===== CABEÇALHO ===== -->
      <div class="card-header bg-white border-bottom-0 pb-0">
        <div class="d-flex align-items-start flex-wrap">
          <!-- Fotos dos parlamentares -->
          <div
            class="emenda-parlamentares-fotos d-flex flex-wrap mr-3 mb-1"
            v-if="registro.parlamentares_valor && registro.parlamentares_valor.length"
          >
            <a
              v-for="p in registro.parlamentares_valor"
              :key="p.id"
              class="emenda-avatar"
              :title="p.__str__"
            >
              <img :src="fotoThumb(p.fotografia)" :alt="p.__str__">
            </a>
          </div>

          <!-- Título e badges -->
          <div class="flex-grow-1">
            <h4 class="mb-1 font-weight-bold">
              <a :href="registro.link_detail_backend" target="_blank">
                {{ registro.oficio_ajuste_loa.__str__ || 'Registro de Ajuste' }}
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

          <!-- Valor -->
          <div
            v-if="registro.str_valor"
            class="text-center ml-auto p-2 mr-3 rounded hover"
          >
            <span class="emenda-valor font-weight-bold text-primary">
              R$ {{ registro.str_valor }}
            </span>
            <br>
            <small class="text-muted">Valor do Ajuste</small>
          </div>
        </div>
      </div>

      <hr class="my-0">

      <!-- ===== DADOS PRINCIPAIS ===== -->
      <div class="card-body pt-2 pb-2">
        <div class="row">
          <div class="col-md-12">
            <small class="d-block text-muted" v-if="registro.unidade">
              <strong>Unidade Orçamentária:</strong>
              <button
                class="btn btn-link btn-sm p-0 align-baseline"
                @click="$emit('filter-unidade', registro.unidade)"
              >{{ registro.unidade.__str__ }}</button>
            </small>
            <small class="d-block text-muted" v-if="emendasLoaList.length">
              <strong>Emendas vinculadas:</strong>
              <button
                v-for="(em, idx) in emendasLoaList"
                :key="`emenda_${em.id}_${idx}`"
                  class="btn btn-link btn-sm p-0 align-baseline"
                  @click="$emit('search-emenda', em.text)"
                >{{ em.text }}</button><span v-if="idx < emendasLoaList.length - 1">, </span>
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
          nav-class="emenda-tabs"
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
    emendasLoaList () {
      if (!this.registro.emendaloa) return []
      const lista = Array.isArray(this.registro.emendaloa)
        ? this.registro.emendaloa
        : [this.registro.emendaloa]
      return lista
        .map(e => ({
          id: e.id,
          pkloa: e.loa,
          text: (e.__str__ || '').split('-')[0].trim()
        }))
        .filter(e => e.text)
    }
  },
  methods: {
    faseVariant,
    faseLabel,
    situacaoLabel,
    situacaoVariant,
    fotoThumb (url) {
      if (!url) return ''
      return url.replace(/\.png$/, '.c128.png')
    },
    fetchTabData (registro) {
      this.prestacaoItems = null

      this.utils
        .fetch({
          app: 'loa',
          model: 'prestacaocontaregistro',
          params: {
            registro_ajuste: registro.id,
            get_all: 'True',
            expand: 'prestacao_conta;registro_ajuste'
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

    .emenda-parlamentares-fotos {
      .emenda-avatar {
        display: inline-block;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid #dee2e6;
        transition: border-color 0.2s, transform 0.15s ease;
        margin-right: -10px;

        &:hover {
          border-color: #007bff;
          transform: translateY(-2px) scale(1.1);
          z-index: 2;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }
    }

    h4 a {
      color: inherit;
      text-decoration: none;

      &:hover {
        color: #007bff;
        text-decoration: none;
      }
    }

    .emenda-valor {
      font-size: 1.3rem;
      white-space: nowrap;
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
