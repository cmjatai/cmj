<template>
  <div :class="['item-de-pauta', type]">
    <div :class="['empty-list', materia.id === undefined ? '' : 'd-none']">
      Carregando Matéria...
    </div>
    <voto-parlamentar v-if="votacaoAberta"></voto-parlamentar>

    <div class="status-votacao">
      <div class="votos" v-if="registro && !votacaoAberta && item.tipo_votacao != 4">
        <div class="voto-abs" v-if="registro.numero_abstencoes">
          <span class="valor">{{ registro.numero_abstencoes }}</span>
          <span class="titulo">ABS</span>
        </div>
        <div class="voto-nao">
          <span class="valor">{{ registro.numero_votos_nao }}</span>
          <span class="titulo">NÃO</span>
        </div>
        <div class="voto-sim">
          <span class="valor">{{ registro.numero_votos_sim }}</span>
          <span class="titulo">SIM</span>
        </div>
      </div>
      <div :class="[statusVotacao]">
        <span v-if="votacaoPedidoPrazoAberta">VOTAÇÃO ABERTA PARA PEDIDO DE ADIAMENTO</span>
        <span v-else-if="votacaoAberta">VOTAÇÃO ABERTA</span>
        <span v-else-if="item.resultado">{{ item.resultado }}</span>
        <span v-else>Tramitando</span>
      </div>
    </div>

    <materia-pauta :materia="materia" :type="type"></materia-pauta>

    <div :class="['item-body']"></div>

    <div
      :class="[
        'item-body',
        materia.id !== undefined && materia.anexadas.length > 0
          ? 'col-anexadas'
          : '',
      ]"
    >
      <div class="col-1-body">
        <div class="status-tramitacao">
          <div
            :class="['observacao', nivel(NIVEL3, observacao.length > 0)]"
            v-html="observacao"
          ></div>
        </div>

        <div
          :class="[
            'sub-containers',
            itensLegislacaoCitada.length === 0
              ? 'd-none'
              : 'container-legis-citada',
          ]"
        >
          <div class="title">
            <span> Legislação Citada </span>
          </div>
          <div class="inner">
            <button
              v-for="legis in itensLegislacaoCitada"
              :key="`legiscit${legis.id}`"
              type="button"
              class="btn btn-link"
              data-toggle="modal"
              :data-target="`modal-legis-citada-${legis.id}`"
              @click="modal_legis_citada = legis"
            >
              {{ legis.__str__ }}
            </button>
          </div>
        </div>

        <div
          :class="[
            'sub-containers',
            nivel(NIVEL2, itensDocumentosAcessorios.length > 0),
            itensDocumentosAcessorios.length === 0
              ? 'd-none'
              : 'container-docs-acessorios',
          ]"
        >
          <div class="title">
            <span> Documentos Acessórios </span>
          </div>
          <div class="inner">
            <a
              :href="docs.arquivo"
              class="btn btn-link"
              v-for="docs in itensDocumentosAcessorios"
              :key="`docsacc${docs.id}`"
            >
              {{ docs.__str__ }}
            </a>
          </div>
        </div>
      </div>
      <div class="col-2-body">
        <div
          :class="['sub-containers', nivel(NIVEL1, itensAnexados.length > 0)]"
        >
          <div class="title">
            <span> Matérias Anexadas em Tramitação</span>
          </div>
          <div class="inner">
            <div v-for="anexada in itensAnexados" :key="`${type}${anexada.id}`" >
              <materia-pauta :materia="anexada" :type="type"></materia-pauta>
            </div>
          </div>
        </div>
      </div>
    </div>
    <norma-simple-modal-view
      v-if="modal_legis_citada"
      :html_id="`modal-legis-citada-${modal_legis_citada.id}`"
      :modal_norma="null"
      :idd="modal_legis_citada.norma"
    ></norma-simple-modal-view>
  </div>
</template>
<script>
import MateriaPauta from './MateriaPauta'
import VotoParlamentar from './VotoParlamentar'
import NormaSimpleModalView from '@/components/norma/NormaSimpleModalView'

export default {
  name: 'item-de-pauta',
  props: ['item', 'type'],
  components: {
    MateriaPauta,
    VotoParlamentar,
    NormaSimpleModalView
  },
  data () {
    return {
      app: [
        'materia',
        'norma',
        'sessao'
      ],
      model: [
        'materialegislativa',
        'tramitacao',
        'anexada',
        'autoria',
        'legislacaocitada',
        'documentoacessorio',
        'registrovotacao',
        'registroleitura',
        'votoparlamentar'
      ],
      materia: {},
      tramitacao: {
        ultima: {},
        status: {}
      },
      anexadas: {},
      legislacaocitada: {},
      documentoacessorio: {},
      modal_legis_citada: null,
      registro: null
    }
  },
  watch: {
    'modal_legis_citada': function (nv, ov) {
      const t = this
      if (nv !== null) {
        this.$nextTick()
          .then(() => {
            $(`#modal-legis-citada-${nv.id}`).modal('show')
            $(`#modal-legis-citada-${nv.id}`).on('hidden.bs.modal', function (e) {
              t.modal_legis_citada = null
            })
          })
      }
    },
    item: function (nv, ov) {
      this.$nextTick()
        .then(() => {
          this.registro = null
        })
        .then(() => {
          this.fetchRegistroDeVoto()
        })
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
        return _.orderBy(_.filter(this.anexadas, (o) => o.em_tramitacao), ['data_apresentacao', 'numero'])
      }
    },
    itensLegislacaoCitada: {
      get () {
        return _.orderBy(this.legislacaocitada, 'norma')
      }
    },
    itensDocumentosAcessorios: {
      get () {
        return _.orderBy(this.documentoacessorio, 'data')
      }
    },
    votacaoAberta: {
      get () {
        return this.item.votacao_aberta && this.item.tipo_votacao <= 2
      }
    },
    votacaoPedidoPrazoAberta: {
      get () {
        return this.item.votacao_aberta_pedido_prazo && this.item.tipo_votacao <= 2
      }
    },
    statusVotacao: {
      get () {
        let tipo = ''
        let r = this.item.resultado
        if (this.votacaoAberta) {
          tipo = 'votacao-aberta'
        } else if (r === 'Aprovado') {
          tipo = 'result-aprovado'
        } else if (r === 'Rejeitado') {
          tipo = 'result-rejeitado'
        } else if (r === 'Pedido de Vista') {
          tipo = 'result-vista'
        } else if (r === 'Prazo Regimental') {
          tipo = 'result-prazo'
        }

        return tipo
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
          // TODO: trocar ultima tramitacao pela fixada na ordem do dia.
          // t.fetchUltimaTramitacao()
        })
        .then(() => {
          t.fetchLegislacaoCitada()
        })
        .then(() => {
          t.fetchDocumentoAcessorio()
        })
        .then(() => {
          t.fetchRegistroDeVoto()
        })
    },
    fetch (metadata) {
      // chamado pelo push do servidor
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
      } else if (metadata.app === 'norma' && metadata.model === 'legislacaocitada') {
        t.fetchLegislacaoCitada()
      } else if (metadata.app === 'materia' && metadata.model === 'documentoacessorio') {
        t.fetchDocumentoAcessorio()
      } else if (metadata.app === 'sessao' && ['registrovotacao', 'registroleitura', 'votoparlamentar'].includes(metadata.model)) {
        t.fetchRegistroDeVoto(metadata)
      }
    },
    async fetchRegistroDeVoto (metadata) {
      const t = this
      const model = t.item.tipo_votacao === 4 ? 'registroleitura' : 'registrovotacao'
      const field = t.type === 'expedientemateria' ? 'expediente' : 'ordem'

      if (t.item.resultado.length > 0 && t.registro === null) {
        const query_string = `&${field}=${t.item.id}&o=-id`
        t.utils
          .getModelList('sessao', model, 1, query_string)
          .then((response) => {
            _.each(response.data.results.slice(0, 1), value => {
              t.registro = value
              t.refreshState({
                app: 'sessao',
                model: model,
                value: value,
                id: value.id
              })
            })
          })
          .catch((response) => {
            t.sendMessage(
              { alert: 'danger', message: 'Não foi possível recuperar o Registro de Votos/Leitura.', time: 5 })
          })
      }
      if (!t.nulls.includes(metadata) && !t.nulls.includes(t.registro) && t.registro.id === metadata.id) {
        t.getObject(metadata)
          .then(obj => {
            if (t.nulls.includes(obj)) {
              t.registro = null
            } else if (obj.materia === t.item.materia) {
              t.registro = obj
            }
          })
      }
    },
    fetchDocumentoAcessorio (page = 1) {
      const t = this
      const query_string = `&materia=${t.item.materia}`
      t.utils
        .getModelList('materia', 'documentoacessorio', page, query_string)
        .then((response) => {
          _.each(response.data.results, value => {
            t.$set(t.documentoacessorio, value.id, value)
          })
          if (response.data.pagination.next_page !== null) {
            t.$nextTick()
              .then(function () {
                t.fetchDocumentoAcessorio(response.data.pagination.next_page)
              })
          }
        })
        .catch((response) => {
          t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a lista de Documentos Acessórios.', time: 5 })
        })
    },
    fetchLegislacaoCitada (page = 1) {
      const t = this
      const query_string = `&materia=${t.item.materia}`
      t.utils
        .getModelList('norma', 'legislacaocitada', page, query_string)
        .then((response) => {
          _.each(response.data.results, value => {
            t.$set(t.legislacaocitada, value.id, value)
          })
          if (response.data.pagination.next_page !== null) {
            t.$nextTick()
              .then(function () {
                t.fetchLegislacaoCitada(response.data.pagination.next_page)
              })
          }
        })
        .catch((response) => {
          t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar a lista de Legislação Citada.', time: 5 })
        })
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
          if (t.tramitacao.ultima.id === undefined) {
            return
          }

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
  padding: 15px;
  //padding-top: 0;
  margin-bottom: 1em;
  border-top: 1px solid #ccc;

  .status-votacao {
    position: absolute;
    display: flex;
    top: -0.7em;
    right: 0;
    font-weight: bold;
    color: #fff;
    line-height: 1;

    & > div  {
      background-color: #e6bc02;
      display: flex;
      padding: 2px 10px 1px;
      align-items: center;
    }
    .votos {
      opacity: 0.3;
      background-color: transparent;
      padding: 0;
      div {
        padding: 2px 10px 1px;
        display: flex;
        gap: 2px;
        .titulo {
          font-size: 60%;
        }
        .valor {
          font-size: 130%;
          padding-right: 5px;
        }
      }
      .voto-sim {
        background-color: #00800099;
        .titulo, .valor {
        }
      }
      .voto-nao {
        background-color: #ff000099;
        .titulo, .valor {
        }
      }
      .voto-abs {
        background-color: #e6bc0299;
        .titulo, .valor {
        }
      }
    }
    .result-aprovado {
      background-color: green;
    }
    .result-prazo {
      background-color: #2580f7;
    }
    .result-vista {
      background-color: #2580f7;
    }
    .result-rejeitado {
      background-color: red;
    }
    .votacao-aberta {
      background-color: #000;
    }
  }

  &:hover {
    background-color: #d6e6fd;
    .votos {
      opacity: 1;
      background-color: #fff;
    }
  }

  &::before {
    content: "Ordem do Dia";
    position: absolute;
    bottom: 1px;
    right: 5px;
    color: rgba(#000, 0.1);
    font-size: 200%;
    display: inline-block;
    line-height: 1;
  }

  &.expedientemateria {
    background-color: #ffffe3;
    &:hover {
      background-color: #f5d576;
    }
    &::before {
      content: "Grande Expediente";
    }
  }

  .sub-containers {
    font-size: 85%;
    margin: 0 -15px 15px -15px;

    .title {
      border-bottom: 1px solid #9ccef7;
      font-size: 130%;
      //display: block;
      //line-height: 1;
      //margin: 0 -1em 0.4em -1em;
      span {
        padding: 0.35em 1em 0.15em;
        //line-height: 1;
        font-weight: bold;
        color: white;
        background-color: #55d651;
        display: inline-block;
      }
    }
    .inner {
      & > .btn-link {
        text-align: left;
        display: inline-block;
        width: 100%;
        //border-bottom: 1px solid #ddd;
        color: #444;
      }
    }
    .materia-pauta {
      border-bottom: 1px solid #fff;
        border-top: 1px solid transparent;
      padding: 10px 15px 0;
      &:hover {
        border-top: 1px solid #bbb;
        background-color: #0001;
      }
      .epigrafe {
        color: #09a503;
      }
      .ementa {
        color: #114b3f;
      }
      .protocolo-data, .autoria {
        padding-top: 0;
        padding-bottom: 0;
      }
    }
  }
  .status-tramitacao {
    font-size: 1em;
    padding-bottom: 15px;
    .observacao {
      display: inline-block;
      border-top: 1px solid #71ca56;
      margin: 0.5em 1em 0 0;
      padding-top: 0.5em;
      line-height: 1.3;
    }
    .ultima_tramitacao {
      line-height: 1.3;
      strong:first-child {
        padding-top: 0.5em;
        border-top: 1px solid #5696ca;
      }
    }
  }

  .sub-containers__old {
    .container-legis-citada {
      //border-top: 1px solid #5696ca;
      button {
        text-align: left;
      }
    }

    .item-body {
      display: grid;
      grid-column-gap: 1em;

      &.col-anexadas {
        grid-template-columns: auto;
      }
    }
  }
}

@media screen and (max-width: 600px) {
  .item-de-pauta {
    .status-votacao {
      line-height: 1;
    }
  }
}

@media screen and (max-width: 480px) {
  .item-de-pauta {
    font-size: 75%;
    padding: 15px 5px 0;
    .item-header {
      .epigrafe {
        letter-spacing: 0px;
      }
    }
  }
}
</style>
