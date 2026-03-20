<template>
  <div class="pcl-detalhe-registro">
    <template v-if="registro">
      <div class="card mb-3 card-detalhe-registro">
        <div
          class="card-header d-flex align-items-center justify-content-between py-2"
        >
          <div>
            <b-badge :variant="itemBadgeVariant(registro)" class="mr-2">
              {{ registroBadgeLabel(registro) }}
            </b-badge>
            <span class="font-weight-bold card-header-title">Prestação de Contas</span>
          </div>
          <a
            :href="registro.link_detail_backend"
            target="_blank"
            class="btn btn-lg btn-link m-0 p-0 text-decoration-none font-weight-bold"
            title="Abrir detalhes no painel administrativo"
          >
            {{ isEmenda(registro) && emendaParts[0] ? emendaParts[0].trim() : 'Abrir' }} <i class="fas fa-external-link-alt ml-3"></i>
          </a>
        </div>
        <div class="card-body py-2">
          <div
            class="d-flex align-items-center mb-2 justify-content-between"
            v-if="registro.parlamentares && registro.parlamentares.length"
          >
            <div class="d-flex align-items-center">
              <div class="avatar-stack mr-2">
                <img
                  v-for="p in registro.parlamentares"
                  :key="p.id"
                  :src="fotoThumb(p.fotografia)"
                  :alt="p.__str__"
                  :title="p.__str__"
                  class="avatar-stack-item"
                />
              </div>
              <div class="parlamentar-names">
                <span
                  v-for="(p, idx) in registro.parlamentares"
                  :key="p.id"
                  class="parlamentar-name"
                >{{ p.__str__ }}<template v-if="idx < registro.parlamentares.length - 1">, </template></span>
              </div>
            </div>
            <h2 :class="['font-weight-bold', 'mb-0', 'ml-2', 'text-nowrap', 'text-' + faseVariant(registro.fase)]" v-if="emendaParts[1]">R$ {{ registro.str_valor_computado }}</h2>
          </div>
          <p class="mb-2" v-if="isEmenda(registro)">
            {{ registro.finalidade }}
          </p>
          <p class="mb-2" v-else>
            {{ registro.descricao }}
          </p>
          <div
            class="row small text-muted mt-1"
            v-if="registro.unidade"
          >
            <div class="col-12" v-if="registro.emendaloa">
              <strong>Vinculado à Emenda:</strong>
              {{ registro.emendaloa.__str__ }}
            </div>
            <div class="col-12" v-if="registro.unidade">
              <i class="fas fa-building mr-1"></i>
              <strong>Unidade Orçamentária:</strong>
              {{ registro.unidade.__str__ }}
            </div>

            <template v-if="isEmenda(registro) && registro.entidade">
              <div class="col-12" v-if="registro.entidade.nome_fantasia">
                <i class="fas fa-user mr-1"></i>
                <strong>Beneficiário:</strong>
                {{ registro.entidade.nome_fantasia }}
              </div>
              <div class="col-12" v-if="cpfcnpjLimpo(registro.entidade.cpfcnpj) || registro.entidade.cnes">
                <i class="fas fa-id-card mr-1"></i>
                <strong>{{ cpfcnpjLimpo(registro.entidade.cpfcnpj) ? 'CPF/CNPJ' : 'CNES' }}:</strong>
                {{ cpfcnpjLimpo(registro.entidade.cpfcnpj) || registro.entidade.cnes }}
              </div>
            </template>
          </div>
        </div>
      </div>

      <b-tabs
        v-if="showTabs"
        class="pcl-tabs-detalhe"
        content-class="mt-0"
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
                >{{ prestacaoItems.length }}</b-badge
              >
            </template>
            <pcl-tab-prestacao :items="prestacaoItems" :registro="registro" />
          </b-tab>

          <b-tab
            v-if="tab.key === 'ajustes'"
            :key="tab.key"
            :active="index === 0"
          >
            <template #title>
              Ajustes vinculados à Emenda
              <b-badge
                variant="secondary"
                pill
                class="ml-1"
                v-if="ajustesItems"
                >{{ ajustesItems.length }}</b-badge
              >
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
                >{{ documentosItems.length }}</b-badge
              >
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
                >{{ tramitacoesItems.length }}</b-badge
              >
            </template>
            <pcl-tab-tramitacoes :items="tramitacoesItems" />
          </b-tab>
        </template>
      </b-tabs>
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
  faseVariant
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
    emendaParts () {
      if (!this.registro || !this.isEmenda(this.registro) || !this.registro.__str__) return []
      const str = this.registro.__str__
      const i1 = str.indexOf('-')
      if (i1 === -1) return [str, '', '']
      const i2 = str.indexOf('-', i1 + 1)
      if (i2 === -1) return [str.substring(0, i1), str.substring(i1 + 1), '']
      return [str.substring(0, i1), str.substring(i1 + 1, i2), str.substring(i2 + 1)]
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
$border-color: #fff;

.avatar-stack {
  display: flex;
  flex-direction: row;

  &-item {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid $border-color;
    box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
    margin-right: -10px;
    transition: transform 0.15s ease, z-index 0s;
    position: relative;
    z-index: 1;

    &:last-child {
      margin-right: 0;
    }

    &:hover {
      transform: translateY(-2px) scale(1.1);
      z-index: 2;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
  }
}

.parlamentar {
  &-names {
    font-size: 0.8rem;
    color: #555;
    line-height: 1.2;
    max-width: 200px;
  }

  &-name {
    font-weight: 600;
  }
}

.pcl-detalhe-registro {
  position: sticky;
  top: 1rem;
  align-self: flex-start;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  .card-header {
    border-bottom: 0;
    .card-header-title {
      font-variant: small-caps;
    }
  }
}

.pcl-tabs-detalhe ::v-deep {

  .nav-tabs {
    border-bottom: 1px solid $border-color;
    .nav-link {
      font-size: 0.85rem;
      font-weight: 600;
      color: #555;
      padding: 0.4rem 0.75rem;

      &.active {
        color: #212529;
        border-color: $border-color;
      }
    }
  }

  .tab-content {
    border: 1px solid $border-color;
    border-top: none;
    border-radius: 0 0 0.25rem 0.25rem;
  }
}
</style>
