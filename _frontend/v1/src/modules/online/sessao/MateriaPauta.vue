<template>
  <div :class="['materia-pauta']">
    <a :href="materia.link_detail_backend" target="_blank" class="epigrafe"
      >{{ tipo_string }} n&#186; {{ materia.numero }}/{{ materia.ano }}</a
    >

    <div :class="['item-header', tipo_string ? '' : 'd-none']">
      <div class="link-file" :id="`${type}-${materia.id}`">
        <a
          :class="[
            'btn btn-link',
            `link-file-${materia.id}`,
            !blob ? 'd-none' : '',
          ]"
          @click="clickFile"
        >
          <i class="far fa-2x fa-file-pdf"></i>
        </a>
        <a
          :class="[
            'btn btn-link',
            `link-file-${materia.id}`,

          ]"
          :href="materia.texto_original"
          target="_blank"
        >
          <i class="far fa-2x fa-file-pdf"></i>
        </a>
        <small :class="!baixando ? 'd-none' : ''">Baixando<br />Arquivo</small>
      </div>

      <div class="data-header">
        <div class="detail-header">
          <div class="protocolo-data">
            <span>
              Protocolo:
              <strong>{{ materia.numero_protocolo }}</strong>
            </span>
            <span>{{ data_apresentacao }}</span>
          </div>
          <div class="autoria">
            <span v-for="(autores, key) in autores_list" :key="`au${key}`">{{
              autores.nome
            }}</span>
          </div>
        </div>
        <div class="ementa" v-html="materia.ementa"></div>

        <div v-if="true" class="status-tramitacao">
          <div
            :class="[
              'ultima_tramitacao',
              nivel(NIVEL2, tramitacao.ultima !== null),
            ]"
          >
            <strong>Situação:</strong> {{ tramitacao.status.descricao }}<br />
            <strong>Ultima Ação:</strong> {{ tramitacao.ultima.texto }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
// import axios from 'axios'
export default {
  name: 'materia-pauta',
  props: ['materia', 'type'],
  data () {
    return {
      app: ['materia'],
      model: ['materialegislativa', 'tramitacao', 'anexada', 'autoria'],
      autores: {},
      tramitacao: {
        ultima: {},
        status: {}
      },
      tipo_string: '',
      blob: null,
      baixando: false
    }
  },
  watch: {
    materia: function (nv) {
      const t = this
      t.refresh()
    }
  },
  computed: {
    data_apresentacao () {
      try {
        const data = this.stringToDate(
          this.materia.data_apresentacao,
          'yyyy-mm-dd',
          '-'
        )
        return `${data.getDate()}/${data.getMonth() + 1}/${data.getFullYear()}`
      } catch (Exception) {
        return ''
      }
    },
    autores_list: {
      get () {
        return _.orderBy(this.autores, 'nome')
      }
    }
  },
  mounted () {
    const t = this
    if (!t.blob && t.materia.id !== undefined) {
      t.refresh()
    }
    /*
    setTimeout(() => {
      if (!t.blob) {
        t.refresh()
      }
    }, 1000) */
  },
  methods: {

    fetchUltimaTramitacao () {
      const t = this
      return t.utils
        .getByMetadata({
          action: 'ultima_tramitacao',
          app: 'materia',
          model: 'materialegislativa',
          id: t.materia.id
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
    },
    clickFile (event) {
      const url = window.URL.createObjectURL(this.blob)
      window.location = url
    },
    fetch (metadata) {
      const t = this
      if (
        t.materia !== undefined &&
        t.materia.id === metadata.id &&
        metadata.model === t.model[0]
      ) {
        this.refresh()
      }
    },
    refresh () {
      const t = this

      if (t.materia === undefined || t.materia.id === undefined) {
        return
      }

      t.getObject({
        app: 'materia',
        model: 'tipomaterialegislativa',
        id: t.materia.tipo
      }).then((obj) => {
        t.tipo_string = obj.descricao
      })

      t.$set(t, 'autores', {})

      t.$nextTick().then(() => {
        _.each(t.materia.autores, (value) => {
          t.getObject({
            app: 'base',
            model: 'autor',
            id: value
          }).then((obj) => {
            t.$set(t.autores, obj.id, obj)

            t.fetchUltimaTramitacao()
          })
        })

        /* if (t.materia.texto_original !== null) {
          let url = `${t.materia.texto_original}?u=${parseInt(Math.random() * 65536)}`
          t.baixando = true

          axios({
            url: url,
            method: 'GET',
            responseType: 'blob' // important
          })
            .then((response) => {
              t.baixando = false
              t.blob = new Blob([response.data], { type: 'application/pdf' })
            })
            .catch(() => {
              t.baixando = false
            })
        } */
      })
    }
  }
}
</script>

<style lang="scss">
.materia-pauta {
  .epigrafe {
    color: #044079;
    font-size: 125%;
    font-weight: bold;
    letter-spacing: 0.5px;
  }
  .ementa {
    margin: 0 0 0.5em 0;
    font-size: 135%;
    line-height: 1.4;
    color: #257464;
    text-align: left;
  }
  .item-header {
    //display: grid;
    //grid-template-columns: minmax(0, 50px) auto;
    //align-items: center;
    //grid-column-gap: 1em;
    small {
      text-align: center;
      display: inline-block;
    }
    .link-file {
      float: left;
    }
  }
  .btn-link {
    cursor: pointer;
    margin: 0.5rem 0.5rem 0 -0.5rem;
  }
  .detail-header {
    display: flex;
    font-size: 95%;
    align-items: center;
    flex-flow: row nowrap;

    .protocolo-data {
      flex: 0 0 auto;
      padding: 0.3em 0.5em 0.3em 0;
      span {
        display: inline-block;
        line-height: 2;
        border-right: 1px solid #00000055;
        padding-right: 0.5em;
        padding-left: 0.5em;
      }
      span:first-child {
        color: #800;
        padding-left: 0;
      }
    }
    .autoria {
      font-weight: bold;
      letter-spacing: 0.1px;
      line-height: 1.5;
      font-size: 95%;
      padding: 0.4em 0;
      span {
        display: inline-block;
        white-space: nowrap;
        &:after {
          content: ";";
          padding-right: 0.5em;
        }
      }
      span:last-child:after {
        content: "";
      }
    }
  }
}

@media screen and (max-width: 480px) {

.materia-pauta {
  .btn-link {
    margin: 0.5rem -0.3rem 0 -0.5rem;
  }
}
}
</style>
