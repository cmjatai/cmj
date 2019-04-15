<template>
  <div :class="['item-de-pauta', type]">

    <div :class="['empty-list', materia.id === undefined ? '' : 'd-none']">
        Carregando Matéria...
    </div>

    <materia-pauta :materia="materia" :type="type"></materia-pauta>

    <div :class="['item-body', materia.id !== undefined && materia.anexadas.length > 0 ? 'col-anexadas':'']">
      <div class="col-1-body">

        <div :class="['ultima_tramitacao', nivel(NIVEL2, tramitacao.ultima !== {})]">
          <strong>Situação:</strong> {{tramitacao.status.descricao}}<br>
          <strong>Ultima Ação:</strong> {{tramitacao.ultima.texto}}
        </div>
        <div :class="['observacao', nivel(NIVEL4, observacao.length > 0)]" v-html="observacao"></div>
      </div>
      <div class="col-2-body">
        <div :class="['container-anexadas', nivel(NIVEL2, itensAnexados.length > 0)]">
          <div class="title">
            <span>
              MATÉRIAS ANEXADAS
            </span>
            </div>
          <div class="inner">
            <div v-for="anexada in itensAnexados" :key="`${type}${anexada.id}`">

              <materia-pauta :materia="anexada" :type="type"></materia-pauta>

            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
<script>
import MateriaPauta from './MateriaPauta'
export default {
  name: 'item-de-pauta',
  props: ['item', 'type'],
  components: {
    MateriaPauta
  },
  data () {
    return {
      app: ['materia'],
      model: ['materialegislativa', 'tramitacao', 'anexada', 'autoria'],
      materia: {},
      tramitacao: {
        ultima: {},
        status: {}
      },
      anexadas: {}
    }
  },
  computed: {
    data_apresentacao () {
      try {
        const data = this.stringToDate(this.materia.data_apresentacao, 'yyyy-mm-dd', '-')
        return `${data.getDate()}/${data.getMonth() + 1}/${data.getFullYear()}`
      } catch (Exception) {
        return ''
      }
    },
    observacao () {
      let o = this.item.observacao
      o = o.replace(/^\r\n/g, '')
      o = o.replace(/\r\n/g, '<br />')
      o = o.replace(/\r/g, ' ')
      o = o.replace(/\n/g, '<br />')
      return o
    },
    itensAnexados: {
      get () {
        return _.orderBy(this.anexadas, 'data_apresentacao')
      }
    }
  },
  mounted () {
    this.refresh()
  },
  methods: {
    refresh () {
      const t = this
      t.fetchMateria()
        .then((obj) => {
          _.each(t.materia.anexadas, (value, idx) => {
            t.fetchMateria({
              action: 'post_save',
              app: t.app[0],
              model: t.model[0],
              id: value
            })
          })
        })
      t.$nextTick()
        .then(() => {
          t.fetchUltimaTramitacao()
        })
    },
    fetch (metadata) {
      const t = this

      if (metadata === undefined) {
        return
      }

      if (metadata.app === 'materia' && metadata.model === 'materialegislativa') {
        if (metadata.id === t.item.materia || metadata.id in t.materia.anexadas) {
          t.fetchMateria(metadata)
        }
      } else if (metadata.app === 'materia' && metadata.model === 'anexada') {
        t.$set(t, 'anexadas', {})
        t.refreshState({
          action: '',
          app: t.app[0],
          model: t.model[0],
          id: t.item.materia
        })
          .then((obj) => {
            t.refresh()
          })
      } else if (metadata.app === 'materia' && metadata.model === 'autoria') {
        t.refreshState({
          action: '',
          app: t.app[0],
          model: t.model[0],
          id: t.item.materia
        })
          .then((obj) => {
            t.refresh()
          })
      } else if (metadata.app === 'materia' && metadata.model === 'tramitacao') {
        t.fetchUltimaTramitacao(metadata)
      }
    },
    fetchMateria (metadata) {
      const t = this
      return t
        .getObject({
          action: '',
          app: t.app[0],
          model: t.model[0],
          id: metadata !== undefined ? metadata.id : t.item.materia
        })
        .then(obj => {
          if (obj.id === t.item.materia) {
            t.materia = obj
          } else {
            t.$set(t.anexadas, obj.id, obj)
          }
          return obj
        })
    },
    fetchUltimaTramitacao () {
      const t = this
      return t.utils
        .getByMetadata({
          action: 'ultima_tramitacao',
          app: 'materia',
          model: 'materialegislativa',
          id: t.item.materia
        })
        .then((response) => {
          t.tramitacao.ultima = response.data
          t.getObject({
            action: '',
            app: 'materia',
            model: 'statustramitacao',
            id: t.tramitacao.ultima.status
          })
            .then(obj => {
              t.tramitacao.status = obj
            })
        })
    }
  }
}
</script>

<style lang="scss">

.item-de-pauta {
  position: relative;
  background-color: #ffffff55;
  padding: 1em;
  margin-bottom: 1em;
  border-top: 1px solid #ccc;

  &:hover {
    background-color: #d6e6fd;
  }

  &::before {
    content: 'Ordem do Dia';
    position: absolute;
    bottom: 5px;
    right: 5px;
    color: rgba(#000, 0.1);
    font-size: 200%;
    display: inline-block;
    line-height: 1;
  }

  &.expedientemateria {
      background-color: #ffffe3;
    &:hover {
      background-color: #ffbf00;
    }
    &::before {
      content: 'Grande Expediente';
    }
  }
  .container-anexadas {
    font-size: 85%;
    margin: 1em;

    .title {
      border-bottom: 1px solid #5696ca;
      font-size: 130%;
      font-weight: bold;
      color: white;
      display: block;
      line-height: 1;
      margin: 0 -1em 0.4em -1em;
      span {
        padding: 0.35em 1em 0.15em;
        line-height: 1;
        background-color: #5696ca;
        display: inline-block

      }
    }
    .materia-pauta {
      border-bottom: 1px solid #aaa;
      .epigrafe {
        padding-top: 5px;
      }
    }
  }

  .item-body {
    display: grid;
    grid-column-gap: 1em;

    &.col-anexadas {
      grid-template-columns: auto;
    }
    //

    .observacao {
      display: inline-block;
      border-top: 1px solid #5696ca;
      margin: 0.5em 1em 0 0;
      padding-top: 0.5em;
      line-height: 1.3;
    }
    .ultima_tramitacao {
      border-top: 1px solid #5696ca;
      padding-top: 0.5em;
      line-height: 1.3;
    }
  }

}

@media screen and (max-width: 480px) {
  .item-de-pauta {
    font-size: 85%;
    .item-header {
      .epigrafe {
        letter-spacing: 0px;
      }
    }
  }
}
</style>
