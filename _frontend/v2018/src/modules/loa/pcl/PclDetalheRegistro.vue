<template>
  <div class="pcl-detalhe-registro">
    <template v-if="registro">
      <div class="emenda-card card border-0 shadow-sm mb-3">

        <!-- ===== CABEÇALHO ===== -->
        <div class="card-header bg-white border-bottom-0 pb-0">
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
              >
                <img :src="fotoThumb(p.fotografia)" :alt="p.__str__">
              </a>
            </div>

            <!-- Título e badges -->
            <div class="flex-grow-1">
              <h4 class="mb-1 font-weight-bold">
                <a :href="registro.link_detail_backend" target="_blank">
                  {{ tituloRegistro }}
                  <i class="fas fa-external-link-alt fa-sm ml-1 text-muted"></i>
                </a>
              </h4>
              <div class="mb-2">
                <span
                  :class="['badge', 'mr-1', 'badge-' + itemBadgeVariant(registro)]"
                >{{ registroBadgeLabel(registro) }}</span>
                <span
                  :class="['badge', 'badge-' + faseVariant(registro.fase)]"
                >{{ faseLabel(registro.fase) }}</span>
              </div>
            </div>

            <!-- Valor -->
            <div
              class="emenda-valor-group d-flex text-center ml-auto hover p-2 mr-3 rounded"
              v-if="isEmenda(registro)"
            >
              <div :class="{ 'zoom08': hasAjustes }">
                <span class="emenda-valor font-weight-bold text-primary">
                  R$ {{ registro.str_valor || registro.str_valor_computado }}
                </span>
                <br>
                <small class="text-muted">Valor Original da Emenda</small>
              </div>
              <div class="valor-computado" v-if="hasAjustes">
                <span class="emenda-valor font-weight-bold text-success">
                  R$ {{ registro.str_valor_computado }}
                </span>
                <br>
                <small class="text-muted">Valor Final após Ajustes</small>
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
              <template v-if="isEmenda(registro) && registro.entidade">
                <small class="text-muted" v-if="registro.entidade.nome_fantasia">
                  <strong>Entidade:</strong> {{ registro.entidade.nome_fantasia }}
                </small>
                <small class="text-muted" v-if="registro.entidade.cnes">
                  <strong>- CNES:</strong> {{ registro.entidade.cnes }}
                </small>
                <small class="text-muted" v-else-if="cpfcnpjLimpo(registro.entidade.cpfcnpj)">
                  <strong>- CPF/CNPJ:</strong> {{ cpfcnpjLimpo(registro.entidade.cpfcnpj) }}
                </small>
              </template>
            </div>
          </div>

          <!-- Finalidade / Descrição -->
          <div class="mt-2 p-2 bg-light rounded border" v-if="textoFinalidade">
            <small class="text-muted">
              <strong>{{ isEmenda(registro) ? 'Finalidade' : 'Descrição' }}:</strong>
              {{ textoFinalidade }}
            </small>
            <template v-if="hasAjustes">
              <br>
              <small class="badge badge-warning text-wrap">
                <strong>Atenção:</strong> Esta emenda possui ajustes técnicos cadastrados.
                Verifique a aba "Ajustes Técnicos" para mais detalhes.
              </small>
            </template>
          </div>
        </div>

        <!-- ===== ABAS ===== -->
        <div class="bg-white p-0 mt-2" v-if="showTabs">
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
    </template>
    <div v-else class="text-muted text-center py-5">
      Selecione uma emenda ou ajuste para ver os registros de prestação de
      contas.
    </div>
  </div>
</template>

<script>
import {
  itemBadgeVariant,
  registroBadgeLabel,
  isEmenda,
  faseVariant,
  faseLabel
} from './utils/pcl-helpers'
import PclTabPrestacao from './tabs/PclTabPrestacao.vue'
import PclTabAjustes from './tabs/PclTabAjustes.vue'
import PclTabDocumentos from './tabs/PclTabDocumentos.vue'
import PclTabTramitacoes from './tabs/PclTabTramitacoes.vue'

export default {
  name: 'pcl-detalhe-registro',
  components: {
    PclTabPrestacao,
    PclTabAjustes,
    PclTabDocumentos,
    PclTabTramitacoes
  },
  props: {
    registro: {
      type: Object,
      default: null
    },
    prestacaoItems: {
      type: Array,
      default: null
    },
    ajustesItems: {
      type: Array,
      default: null
    },
    documentosItems: {
      type: Array,
      default: null
    },
    tramitacoesItems: {
      type: Array,
      default: null
    }
  },
  computed: {
    showTabs () {
      if (!this.registro) return false
      // Emendas modificativas (tipo === 0) não exibem tabs
      return !this.isEmenda(this.registro) || this.registro.tipo !== 0
    },
    tituloRegistro () {
      if (!this.registro) return ''
      if (this.isEmenda(this.registro)) {
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
        return this.emendaParts[0] ? this.emendaParts[0].trim() : this.registroBadgeLabel(this.registro)
      }
      return this.registro.descricao || 'Registro de Ajuste'
    },
    hasAjustes () {
      if (!this.registro) return false
      if (this.registro.has_ajustes !== undefined) return this.registro.has_ajustes
      return Array.isArray(this.ajustesItems) && this.ajustesItems.length > 0
    },
    textoFinalidade () {
      if (!this.registro) return ''
      if (this.isEmenda(this.registro)) return this.registro.ementa_format || ''
      return this.registro.descricao || ''
    },
    emendaParts () {
      if (!this.registro || !this.isEmenda(this.registro) || !this.registro.__str__) return []
      const str = this.registro.__str__
      const i1 = str.indexOf('-')
      if (i1 === -1) return [str, '', '']
      const i2 = str.indexOf('-', i1 + 1)
      if (i2 === -1) return [str.substring(0, i1), str.substring(i1 + 1), '']
      return [str.substring(0, i1), str.substring(i1 + 1, i2), str.substring(i2 + 1)]
    },
    emendasLoaFormatadas () {
      if (!this.registro || !this.registro.emendaloa) return ''
      const lista = Array.isArray(this.registro.emendaloa)
        ? this.registro.emendaloa
        : [this.registro.emendaloa]
      return lista
        .map(e => (e.__str__ || '').split('-')[0].trim())
        .filter(s => s)
        .join(', ')
    },
    orderedTabs () {
      const tabs = []
      const emenda = this.isEmenda(this.registro)

      tabs.push({
        key: 'prestacao',
        hasData:
          Array.isArray(this.prestacaoItems) && this.prestacaoItems.length > 0
      })

      if (emenda) {
        tabs.push({
          key: 'ajustes',
          hasData:
            Array.isArray(this.ajustesItems) && this.ajustesItems.length > 0
        })
      }

      if (emenda && this.registro.materia) {
        tabs.push({
          key: 'tramitacoes',
          hasData:
            Array.isArray(this.tramitacoesItems) &&
            this.tramitacoesItems.length > 0
        })
        tabs.push({
          key: 'documentos',
          hasData:
            Array.isArray(this.documentosItems) &&
            this.documentosItems.length > 0
        })
      }

      return tabs.sort((a, b) => (b.hasData ? 1 : 0) - (a.hasData ? 1 : 0))
    }
  },
  methods: {
    itemBadgeVariant,
    registroBadgeLabel,
    isEmenda,
    faseVariant,
    faseLabel,
    fotoThumb (url) {
      if (!url) return ''
      return url.replace(/\.png$/, '.c128.png')
    },
    cpfcnpjLimpo (val) {
      if (!val) return ''
      return val.replace(/[0\s]/g, '') ? val.trim() : ''
    }
  }
}
</script>

<style lang="scss" scoped>
.pcl-detalhe-registro {
  position: sticky;
  top: 1rem;
  align-self: flex-start;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
}

.pcl-detalhe-registro ::v-deep {
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
</style>
