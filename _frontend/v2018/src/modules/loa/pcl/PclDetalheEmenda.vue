<template>
  <div class="pcl-detalhe-emenda">
    <div :class="['emenda-card', 'card', 'shadow-sm', 'mb-3', emendaTipoClass]">

      <!-- ===== CABEÇALHO ===== -->
      <div :class="['card-header', 'border-bottom-0', 'pb-0']">
        <div class="d-flex align-items-start flex-wrap">
          <!-- Fotos dos parlamentares -->
          <div
            class="emenda-parlamentares-fotos d-flex flex-wrap mr-3 mb-1"
            v-if="registro.parlamentares && registro.parlamentares.length"
          >
            <a
              v-for="p in registro.parlamentares"
              :key="p.id"
              class="emenda-avatar"
              :title="p.__str__"
              href="#"
              @click.prevent="$emit('filter-parlamentar', p)"
            >
              <img :src="fotoThumb(p.fotografia)" :alt="p.__str__">
            </a>
          </div>

          <!-- Título e badges -->
          <div class="flex-grow-1">
            <h3 class="mb-1 font-weight-bold text-wrap text-primary">
              <a :href="registro.link_detail_backend" target="_blank">
                {{ tituloRegistro }}
                <i class="fas fa-external-link-alt fa-sm ml-1 text-muted"></i>
              </a>
            </h3>
            <div class="mb-2">
              <span
                :class="['badge', 'mr-1', 'badge-' + tipoVariant(registro.tipo)]"
              >
                <i :class="tipoIcon" class="mr-1"></i>{{ tipoLabel(registro.tipo) }}
              </span>
              <span
                :class="['badge', 'mr-1', 'badge-' + faseVariant(registro.fase)]"
              >{{ faseLabel(registro.fase) }}</span>
            </div>
          </div>

          <!-- Valor -->
          <div
            class="emenda-valor-group d-flex text-center ml-auto hover p-2 mr-3 rounded"
          >
            <div :class="{ 'zoom08': hasAjustes }">
              <span class="emenda-valor font-weight-bold text-primary">
                R$ {{ registro.str_valor || registro.str_valor_computado }}
              </span>
              <br>
              <small class="text-muted">Valor Original da Emenda</small>
            </div>
            <div class="valor-computado" v-if="hasAjustes || !registro.valor_computado">
              <span class="emenda-valor font-weight-bold text-success">
                R$ {{ registro.str_valor_computado }}
              </span>
              <br>
              <small class="text-muted" v-if="registro.valor_computado">Valor Final após Ajustes</small>
              <small class="text-muted" v-else>Emenda Redefinida nos Ajustes</small>
            </div>
          </div>
        </div>
      </div>

      <hr class="my-0 mx-2">

      <!-- ===== DADOS PRINCIPAIS ===== -->
      <div class="card-body pt-2 pb-2">
        <div class="row">
          <div class="col-md-12">
            <small class="d-block text-muted" v-if="registro.unidade">
              <strong><i class="fas fa-building mr-1"></i>Unidade Orçamentária: </strong>
              <button
                class="btn btn-link btn-sm p-0 align-baseline"
                @click="$emit('filter-unidade', registro.unidade)"
              >{{ registro.unidade.__str__ }}</button>
            </small>
            <template v-if="registro.entidade">
              <small class="text-muted" v-if="registro.entidade.nome_fantasia">
                <strong><i class="fas fa-hand-holding-heart mr-1"></i>Beneficiário: </strong>
                <button
                  class="btn btn-link btn-sm p-0 align-baseline"
                  @click="$emit('filter-entidade', registro.entidade)"
                >{{ registro.entidade.nome_fantasia }}</button>
              </small>
              <small class="text-muted" v-if="registro.entidade.cnes">
                <strong> - CNES:</strong> {{ registro.entidade.cnes }}
              </small>
              <small class="text-muted" v-else-if="cpfcnpjLimpo(registro.entidade.cpfcnpj)">
                <strong> - CPF/CNPJ:</strong> {{ cpfcnpjLimpo(registro.entidade.cpfcnpj) }}
              </small>
            </template>
          </div>
        </div>

        <!-- Objeto -->
        <div class="mt-2 p-2 bg-light rounded border" v-if="registro.ementa_format">
          <small class="text-muted">
            <strong>Objeto Inicial:</strong>
            <span :class="[hasAjustes && registro.valor_computado ? 'text-decoration-line-through' : '']">
              {{ registro.ementa_format }}
            </span>
          </small>
          <template v-if="hasAjustes">
            <hr class="my-2">
            <small class="badge badge-warning text-wrap">
              <strong>Atenção!</strong>
            </small>
            <small class="text-muted  mt-1">
              Esta emenda possui ajustes técnicos cadastrados.
              Verifique a aba "Ajustes Técnicos" para mais detalhes.
            </small>
          </template>
        </div>
      </div>

      <!-- ===== ABAS ===== -->
      <div class="bg-white p-0 mt-2" v-if="registro.tipo !== 0">
        <b-tabs
          nav-class="nav-fill emenda-tabs"
          content-class="p-0"
          small
        >
          <template v-for="(tab, index) in orderedTabs">
            <b-tab
              v-if="tab.key === 'prestacao'"
              :key="tab.key"
              :active="index === 0"
            >
              <template #title>
                Prestação de Contas
                <b-badge
                  variant="secondary"
                  pill
                  class="ml-1"
                  v-if="prestacaoItems"
                >{{ prestacaoItems.length }}</b-badge>
              </template>
              <pcl-tab-prestacao :items="prestacaoItems" :registro="registro" />
            </b-tab>

            <b-tab
              v-if="tab.key === 'ajustes'"
              :key="tab.key"
              :active="index === 0"
            >
              <template #title>
                Ajustes Técnicos
                <b-badge
                  variant="secondary"
                  pill
                  class="ml-1"
                  v-if="ajustesItems"
                >{{ ajustesItems.length }}</b-badge>
              </template>
              <pcl-tab-ajustes :items="ajustesItems" />
            </b-tab>

            <b-tab
              v-if="tab.key === 'documentos'"
              :key="tab.key"
              :active="index === 0"
            >
              <template #title>
                Documentos Acessórios
                <b-badge
                  variant="secondary"
                  pill
                  class="ml-1"
                  v-if="documentosItems"
                >{{ documentosItems.length }}</b-badge>
              </template>
              <pcl-tab-documentos :items="documentosItems" />
            </b-tab>

            <b-tab
              v-if="tab.key === 'tramitacoes'"
              :key="tab.key"
              :active="index === 0"
            >
              <template #title>
                Tramitações
                <b-badge
                  variant="secondary"
                  pill
                  class="ml-1"
                  v-if="tramitacoesItems"
                >{{ tramitacoesItems.length }}</b-badge>
              </template>
              <pcl-tab-tramitacoes :items="tramitacoesItems" />
            </b-tab>
          </template>
        </b-tabs>
      </div>

    </div>
  </div>
</template>

<script>
import {
  itemBadgeVariant,
  registroBadgeLabel,
  faseVariant,
  faseLabel,
  tipoVariant,
  tipoLabel
} from './utils/pcl-helpers'
import PclTabPrestacao from './tabs/PclTabPrestacao.vue'
import PclTabAjustes from './tabs/PclTabAjustes.vue'
import PclTabDocumentos from './tabs/PclTabDocumentos.vue'
import PclTabTramitacoes from './tabs/PclTabTramitacoes.vue'

export default {
  name: 'pcl-detalhe-emenda',
  components: {
    PclTabPrestacao,
    PclTabAjustes,
    PclTabDocumentos,
    PclTabTramitacoes
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
      ajustesItems: null,
      documentosItems: null,
      tramitacoesItems: null,
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
    emendaTipoClass () {
      const v = tipoVariant(this.registro.tipo)
      return `emenda-tipo-${v}`
    },
    emendaHeaderClass () {
      const v = tipoVariant(this.registro.tipo)
      return `emenda-header-${v}`
    },
    tipoIcon () {
      const icons = { 0: 'fas fa-pen-fancy', 10: 'fas fa-heartbeat', 99: 'fas fa-th-large' }
      return icons[this.registro.tipo] || 'fas fa-file-alt'
    },
    tituloRegistro () {
      if (this.registro.materia) {
        const m = this.registro.materia
        if (m.tipo && (m.tipo.sigla || m.tipo.__str__)) {
          const sigla = m.tipo.sigla || ''
          const tipoNome = m.tipo.__str__ || m.tipo.descricao || ''
          const num = String(m.numero || '').padStart(3, '0')
          return `${sigla} ${num}/${m.ano} - ${tipoNome}`
        }
        return m.epigrafe || m.__str__ || this.registro.epigrafe_short || 'Emenda em Elaboração'
      }
      const parts = this.emendaParts
      return parts[0] ? parts[0].trim() : this.registroBadgeLabel(this.registro)
    },
    hasAjustes () {
      if (this.registro.has_ajustes !== undefined) return this.registro.has_ajustes
      return Array.isArray(this.ajustesItems) && this.ajustesItems.length > 0
    },
    emendaParts () {
      if (!this.registro.__str__) return []
      const str = this.registro.__str__
      const i1 = str.indexOf('-')
      if (i1 === -1) return [str, '', '']
      const i2 = str.indexOf('-', i1 + 1)
      if (i2 === -1) return [str.substring(0, i1), str.substring(i1 + 1), '']
      return [str.substring(0, i1), str.substring(i1 + 1, i2), str.substring(i2 + 1)]
    },
    orderedTabs () {
      const tabs = []

      tabs.push({
        key: 'prestacao',
        hasData: Array.isArray(this.prestacaoItems) && this.prestacaoItems.length > 0
      })

      tabs.push({
        key: 'ajustes',
        hasData: Array.isArray(this.ajustesItems) && this.ajustesItems.length > 0
      })

      tabs.sort((a, b) => (b.hasData ? 1 : 0) - (a.hasData ? 1 : 0))

      if (this.registro.materia) {
        tabs.push({
          key: 'tramitacoes',
          hasData: Array.isArray(this.tramitacoesItems) && this.tramitacoesItems.length > 0
        })
        tabs.push({
          key: 'documentos',
          hasData: Array.isArray(this.documentosItems) && this.documentosItems.length > 0
        })
      }
      return tabs
    }
  },
  methods: {
    itemBadgeVariant,
    registroBadgeLabel,
    faseVariant,
    faseLabel,
    tipoLabel,
    tipoVariant,
    fotoThumb (url) {
      if (!url) return ''
      return url.replace(/\.png$/, '.c128.png')
    },
    cpfcnpjLimpo (val) {
      if (!val) return ''
      return val.replace(/[0\s]/g, '') ? val.trim() : ''
    },
    fetchTabData (registro) {
      this.prestacaoItems = null
      this.ajustesItems = null
      this.documentosItems = null
      this.tramitacoesItems = null

      this.utils
        .fetch({
          app: 'loa',
          model: 'prestacaocontaregistro',
          params: {
            emendaloa: registro.id,
            get_all: 'True',
            expand: 'prestacao_conta;registro_ajuste'
          }
        })
        .then((response) => {
          this.prestacaoItems = response.data
        })

      this.utils
        .fetch({
          app: 'loa',
          model: 'registroajusteloa',
          params: {
            emendaloa: registro.id,
            get_all: 'True',
            expand: 'oficio_ajuste_loa;unidade;materia'
          }
        })
        .then((response) => {
          this.ajustesItems = response.data
        })

      if (registro.materia) {
        const materiaId = typeof registro.materia === 'object'
          ? registro.materia.id
          : registro.materia

        this.utils
          .fetch({
            app: 'materia',
            model: 'documentoacessorio',
            params: {
              materia: materiaId,
              get_all: 'True',
              expand: 'tipo'
            }
          })
          .then((response) => {
            this.documentosItems = response.data
          })

        this.utils
          .fetch({
            app: 'materia',
            model: 'tramitacao',
            params: {
              materia: materiaId,
              get_all: 'True',
              expand: 'unidade_tramitacao_local;unidade_tramitacao_destino;status',
              include: 'status.id,__str__;unidade_tramitacao_local.id,__str__;unidade_tramitacao_destino.id,__str__'
            }
          })
          .then((response) => {
            this.tramitacoesItems = response.data
          })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.pcl-detalhe-emenda ::v-deep {
  .emenda-card {
    transition: box-shadow 0.2s;
    border: 0px;
    border-left: 2px solid transparent;

    &.emenda-tipo-info {
      border-left-color: #17a2b8;
    }
    &.emenda-tipo-success {
      border-left-color: #28a745;
    }
    &.emenda-tipo-warning {
      border-left-color: #ffc107;
    }
    &.emenda-tipo-light {
      border-left-color: #dee2e6;
    }

    &:hover {
      box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.12) !important;
    }

    .card-header {
      padding: 1rem;
      background-color: #fff;

      &.emenda-header-info {
        background-color: rgba(23, 162, 184, 0.1);
      }
      &.emenda-header-success {
        background-color: rgba(40, 167, 69, 0.1);
      }
      &.emenda-header-warning {
        background-color: rgba(255, 193, 7, 0.1);
      }
      &.emenda-header-light {
        background-color: #fff;
      }
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

    .emenda-valor-group {
      display: flex;
      align-items: center;
      gap: 3rem;
      line-height: 1;
      margin-bottom: 0.5rem;

      .emenda-valor {
        font-size: 1.3rem;
        white-space: nowrap;
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

/* ===== Responsivo < 992px ===== */
@media (max-width: 991.98px) {
  .pcl-detalhe-emenda ::v-deep {
    .emenda-card .emenda-valor-group {
      flex: 0 0 100%;
      margin-left: 0 !important;
      margin-right: 0 !important;
      margin-top: 0.5rem;
      justify-content: flex-start;
      gap: 1.5rem;
      text-align: left;
    }
  }
}

/* ===== Responsivo < 768px ===== */
@media (max-width: 767.98px) {
  .pcl-detalhe-emenda ::v-deep {
    .emenda-card {
      .card-header {
        padding: 0.75rem;
      }
      h4 {
        font-size: 1rem;
      }
      .emenda-parlamentares-fotos .emenda-avatar {
        width: 38px;
        height: 38px;
      }
      .emenda-valor-group .emenda-valor {
        font-size: 1.05rem;
      }
    }
    .nav-tabs .nav-link {
      font-size: 0.75rem;
      padding: 0.3rem 0.5rem;
    }
    .tab-pane .d-flex.justify-content-between {
      flex-direction: column;
      align-items: flex-start !important;
      gap: 0.25rem;
    }
  }
}

/* ===== Responsivo < 425px ===== */
@media (max-width: 425px) {
  .pcl-detalhe-emenda ::v-deep {
    .emenda-card {
      .card-header {
        padding: 0.5rem;
      }
      h4 {
        font-size: 0.9rem;
      }
      .emenda-parlamentares-fotos .emenda-avatar {
        width: 32px;
        height: 32px;
      }
      .emenda-valor-group {
        flex-direction: column;
        gap: 0.5rem !important;

        .emenda-valor {
          font-size: 0.95rem;
        }
      }
      .card-body {
        padding: 0.5rem;
      }
    }
    .nav-tabs .nav-link {
      font-size: 0.7rem;
      padding: 0.25rem 0.4rem;
    }
    .tab-pane .p-3 {
      padding: 0.5rem !important;
    }
    .tab-pane .px-3 {
      padding-left: 0.75rem !important;
      padding-right: 0.75rem !important;
    }
  }
}
</style>
