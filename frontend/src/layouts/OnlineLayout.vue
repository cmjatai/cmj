<template>
  <base-layout>

    <template slot="brand">
      <brand></brand>
    </template>
    <template slot="header-detail">
        <nivel-detalhe></nivel-detalhe>
        <div class="btn-group ml-2 btn-group-sm accessibility" role="group" aria-label="First group">
          <a class="btn btn-outline-dark" @click="diminuirFonte">a</a>
          <a class="btn btn-outline-dark" @click="aumentarFonte">A</a>
        </div>
    </template>
    <template slot="header-right">
      <i class="fas fa-sign-out-alt hover-circle" @click="close" title="Sair da Interface Sapl Online"></i>
    </template>

    <template slot="sideleft">
      <side-left></side-left>
    </template>

    <template slot="sideright">
      <side-right></side-right>
    </template>

    <template slot="videoconf">
      <video-conferencia></video-conferencia>
    </template>

    <template slot="main">
      <router-view></router-view>
    </template>

  </base-layout>
</template>

<script>
import SideRight from './fragments/SideRight'
import SideLeft from './fragments/SideLeft'
import Brand from './fragments/Brand'
import BaseLayout from './fragments/BaseLayout'
import NivelDetalhe from './NivelDetalhe'
import VideoConferencia from '../pages/sessao/VideoConferencia'

export default {
  name: 'online',
  components: {
    BaseLayout,
    SideRight,
    SideLeft,
    Brand,
    NivelDetalhe,
    VideoConferencia
  },
  data () {
    return {
      models_init_cache: {
        base: ['autor'],
        sessao: [
          'tiposessaoplenaria',
          {
            model: 'expedientesessao',
            full_pages: false,
            ordering: '-sessao_plenaria'
          }
        ],
        materia: ['tipomaterialegislativa', 'statustramitacao'],
        parlamentares: [
          'legislatura',
          {
            model: 'sessaolegislativa',
            full_pages: false,
            ordering: '-data_inicio'
          }
        ]
      }
    }
  },
  mounted: function () {
    this.$connect()
    this.initCache()
  },
  beforeDestroy: function () {
    this.$disconnect()
  },
  methods: {
    diminuirFonte () {
      $('.base-layout .main').css('font-size', '-=1')
    },
    aumentarFonte () {
      $('.base-layout .main').css('font-size', '+=1')
    },
    close () {
      window.location.href = '/'
    },
    fetchList (page = null, _app = null, _model = null) {
      const t = this

      t.utils
        .getModelOrderedList(_app,
          t.isString(_model) ? _model : _model.model,
          t.isString(_model) ? '' : _model.ordering,
          page === null ? 1 : page
        )
        .then((response) => {
          _.each(response.data.results, (_value, idx) => {
            t.refreshState({
              app: _app,
              model: t.isString(_model) ? _model : _model.model,
              id: _value.id,
              value: _value
            })
          })
          t.$nextTick()
            .then(function () {
              if (response.data.pagination.next_page !== null) {
                if (t.isString(_model) || _model.full_pages) {
                  t.fetchList(response.data.pagination.next_page, _app, _model)
                }
              }
            })
        })
    },
    initCache () {
      const t = this
      _.mapKeys(t.models_init_cache, function (model_list, app) {
        _.each(model_list, function (model) {
          t.fetchList(1, app, model)
        })
      })
    }
  }
}
</script>

<style lang="scss">
.header-right {
  display: grid;
  align-items: center;
  justify-items: center;
  i {
    color: rgba(black, 0.5);
    padding: 8px;
    cursor: pointer;
    &:hover {
      color: black;
    }
  }
}
</style>
