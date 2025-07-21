<template>
  <div :class="['materia-pauta']" :id="`mp${type}-${materia.id}`">
    <a :href="materia.link_detail_backend" target="_blank" class="epigrafe"
      >{{ tipo_string }} n&#186; {{ materia.numero }}/{{ materia.ano }}</a
    >

    <div :class="['item-header', tipo_string ? '' : 'd-none']">
      <div class="link-file" :id="`${type}-${materia.id}`" :key="`${type}-${materia.id}`">
        <a
          :class="[
            'btn btn-link',
            `link-file-${materia.id}`,
            !blob ? 'd-none' : '',
          ]"
          @click="clickFile">
          <i class="far fa-2x fa-file-pdf"></i>
        </a>
        <small :class="!baixando ? 'd-none' : ''">Baixando<br />Arquivo</small>
        <a
          :class="[
            'btn btn-link',
            `link-file-${materia.id}`
          ]"
          :href="materia.texto_original"
          target="_blank"
        >
          <i class="far fa-2x fa-file-pdf"></i>
        </a>
        <hr>
        <div class="page-preview" :key="`pp-${type}-${materia.id}`" :id="`pp-${type}-${materia.id}`">
          <div class="btn btn-preview " @click="togglePreview">
            <i :class="['fas fa-eye', preview ? 'd-block':'d-none']"></i>
            <i :class="['far fa-eye-slash', preview ? 'd-none':'d-block']"></i>
          </div>
          <div :class="['preview-online', preview ? 'd-block':'d-none']" :id="`pon-${materia.id}`">
            <span class="p-5">
              Carregando imagem da primeira página da matéria...
            </span>

            <div class="preview-direction">
              <div class="inner-direction btn-group">
                <span class="btn btn-secondary preview-previous" @click="changePage(-1)"  v-show="materia._paginas > 1">
                  <i class="fas fa-chevron-left" aria-hidden="true"><span>Página Anterior</span></i>
                </span>
                <div class="preview-currentpage">
                  <small><em>Página Atual</em></small>
                  <div>
                    <span class="currentpage">{{preview_page}}</span> de <span class="totalpage">{{materia._paginas}}</span>
                  </div>
                </div>
                <span class="btn btn-secondary preview-next" @click="changePage(1)"  v-show="materia._paginas > 1">
                  <i class="fas fa-chevron-right" aria-hidden="true"><span>Próxima Página</span></i>
                </span>
              </div>
            </div>
            <div @click="togglePreview" class="btn btn-danger">X</div>
            <img loading="lazy" :src="`${materia.texto_original}?page=${preview_page}&dpi=190&u=${utimes}`" title="" alt="Preview da Primeira Página do Documento..." class="img-fluid">
            <div class="loading" v-if="preview_loading">
              <div class="loader"></div>
            </div>
          </div>
        </div>
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
      baixando: false,
      preview: false,
      preview_page: 1,
      preview_loading: false,
      paginas_abertas: [],
      utimes: 0
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
    t.$root.$on('closePreviews', (id) => {
      if (t.materia.id !== id) {
        t.preview = false
      }
    })
  },
  methods: {
    changePage (direction) {
      const t = this
      if (t.preview_page + direction > 0 && t.preview_page + direction <= t.materia._paginas) {
        t.preview_page += direction
        t.utimes++

        if (t.preview_page > 1 && !t.paginas_abertas.includes(t.preview_page)) {
          t.preview_loading = true
          setTimeout(() => {
            t.preview_loading = false
            t.paginas_abertas.push(t.preview_page)
          }, 3000)
        }
      }
    },
    togglePreview () {
      const t = this
      t.preview = !t.preview
      t.preview_loading = true && t.preview
      setTimeout(() => {
        t.preview_loading = false
      }, 1000)
      if (t.preview) {
        t.$root.$emit('closePreviews', t.materia.id)
        // scrolling
        setTimeout(() => {
          const preview = document.getElementById(`mp${t.type}-${t.materia.id}`)
          const main = document.getElementsByClassName('main')[0]
          let curtop = 0
          let obj = preview
          do {
            curtop += obj.offsetTop
            obj = obj.offsetParent
          } while (obj && obj.tagName !== 'BODY')
          main.scrollTo({
            top: curtop - 120,
            behavior: 'smooth'
          })
        }, 1000)
      }
    },
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
  position: relative;
  clear: both;
  .btn-link {
    cursor: pointer;
    margin: 0.5rem 0.5rem 0 -0.5rem;
  }
  hr {
    border: 0.5px solid #777;
    margin: 16px 0 0 -15px;
    width: 100%;
  }
  .page-preview {
    .btn.btn-danger {
      position: absolute;
      margin: 5px;
      padding: 0px 15px;
      z-index: 3;
      font-size: 1.5em;
    }
    .btn-preview {
      zoom: 1.3;
      margin: 0.5rem 0.0rem 0.5rem -10px;
      //padding: 10px;
      .fa-eye {
        color: #044079;
      }
    }
    .preview-online {
      position: absolute;
      top: -45px;
      right: -16px;
      left: 60px;
      min-height: 60vh;
      max-height: none;
      box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
      background-color: #fff;
      overflow: auto;
      z-index: 10000;
      margin-bottom: 2em;
      & > span {
        position: absolute;
        z-index: -1;
        top: 0;
        left: 0;
      }
      img {
        z-index: 1;
      }
      .preview-direction {
        position: fixed;
        bottom: 0;
        left: 154px;
        right: 98px;
        display: flex;
        justify-content: center;
        background: linear-gradient(to bottom, #fff0, #ffff);
        padding: 1em;
        .inner-direction {
          display: flex;
          align-items: stretch;
          border-radius: 5px;
        }

        .preview-previous, .preview-next {
          font-size: 2em;
        }
        .preview-previous {
          left: 0;
        }
        .preview-next {
          right: 0;
        }
        .preview-currentpage {
          border: 1px solid #00000055;
          background-color: #ddd;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          gap: 5px;
          padding: 2px 2em;
          .currentpage, .totalpage {
            font-size: 1.5em;
            font-weight: bold;
            color: #044079;
          }
        }
      }
    }
  }
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
    display: grid;
    grid-template-columns: minmax(0, 50px) auto;
    align-items: start;
    grid-column-gap: 0em;
    small {
      text-align: center;
      display: inline-block;
    }
    .link-file {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
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
