<template>
  <div class="arq-doc-item" @mousemove="mouseMove">
    <div class="inner">
      <div class="titulo">
        <i v-if="arqdoc.checkcheck" class="fas fa-xs fa-lock text-light-blue" title="ArqClasse Arquivada."></i>&nbsp;
        <a :href="arqdoc.link_detail_backend" target="_blank">{{ arqdoc.titulo }}</a>
      </div>
      <div class="descricao" v-html="arqdoc.descricao"></div>
      <div class="rodape">
        <span class="data">
          Data do Documento: {{ data_computed }}
        </span>
        <span class="created">
          Inclusão no ArqDoc: {{ created_computed }}
        </span>
      </div>
      <div class="rodape">
        <bread-crumb-classe v-if="contra_classe" :parents="contra_classe.parents" :me="contra_classe"></bread-crumb-classe>
      </div>
      <div class="inner-preview" ref="preview">
        <img v-if="imgdisplay" ref="imgpreview" @error="errorPreview" @load="loadPreview">
        <div class="actions" ref="preview_actions">
          <a class="previous" @click="clickPrevious">
            <i class="fas fa-chevron-left"></i>
          </a>
          <a class="next" @click="clickNext">
            <i class="fas fa-chevron-right"></i>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import axios from 'axios'
import BreadCrumbClasse from './BreadCrumbClasse.vue'

export default {
  name: 'arq-doc-item',
  components: { BreadCrumbClasse },
  props: [ 'arqdoc', 'classe' ],
  data () {
    return {
      imgdisplay: false,
      img_src: null,
      dpi: 72,
      page: 1,
      contra_classe: null,
      ARQCLASSE_FISICA: 100,
      ARQCLASSE_LOGICA: 200
    }
  },
  watch: {
    dpi (nv, old) {
      this.img_src = `${this.arqdoc.arquivo}?page=${this.page}&dpi=${nv}`
    },
    page (nv, old) {
      this.img_src = `${this.arqdoc.arquivo}?page=${nv}&dpi=${this.dpi}`
    },
    img_src (nv, old) {
      const t = this
      t.imgdisplay = true
      t.$nextTick(() => {
        t.$refs.imgpreview.src = nv
      })
    },
    img_src__blob (nv, old) {
      const t = this
      axios({
        url: nv,
        method: 'GET',
        responseType: 'blob' // important
      })
        .then((response) => {
          t.imgdisplay = true
          return response
        })
        .then((response) => {
          const blob = new Blob([response.data], { type: 'image/png' })
          const urlCreator = window.URL || window.webkitURL
          const imageUrl = urlCreator.createObjectURL(blob)
          t.$refs.imgpreview.src = imageUrl
        })
        .catch((e) => {
          if (t.page > 1) {
            t.page -= 1
            t.sendMessage(
              { alert: 'info', message: 'Esta é a última página.', time: 2 })
          } else {
            t.sendMessage(
              { alert: 'info', message: 'Esta é a primeira página.', time: 2 })
          }
        })
    }
  },
  computed: {
    data_computed () {
      return this.arqdoc.data.split('-').reverse().join('/')
    },
    created_computed () {
      return new Date(this.arqdoc.created).toLocaleString()
    }
  },
  methods: {
    loadPreview (event) {
      this.$refs.preview_actions.style.display = 'flex'
    },
    errorPreview (event) {
      if (this.page > 1) {
        this.page -= 1
        this.sendMessage(
          { alert: 'info', message: 'Esta é a última página.', time: 2 })
      } else {
        this.sendMessage(
          { alert: 'info', message: 'Esta é a primeira página.', time: 2 })
      }
    },
    clickPrevious (event) {
      if (this.page > 1) {
        this.page -= 1
      }
    },
    clickNext (event) {
      this.page += 1
    },
    mouseMove (event) {
      if (this.img_src === null) {
        this.img_src = `${this.arqdoc.arquivo}?page=${this.page}&dpi=${this.dpi}`
      }
      let zoom = (event.offsetX + 30) / this.$vnode.elm.offsetWidth
      if (zoom > 0.7) {
        zoom = 0.7
      }
      if (!event.target.closest('.inner-preview')) {
        this.$refs.preview.style.top = `${zoom * -100 / 1.7}vh`
        this.$refs.preview.style.bottom = `${zoom * -100 / 1.7}vh`
      }
      if (zoom > 0.5) {
        this.dpi = 300
      }
    }
  },
  mounted: function () {
    const t = this
    t.$nextTick()
      .then(function () {
        return t.getObject({
          action: '',
          app: 'arq',
          model: 'arqclasse',
          id: t.classe.perfil === t.ARQCLASSE_FISICA ? t.arqdoc.classe_logica : t.arqdoc.classe_estrutural
        })
          .then((classe) => {
            t.contra_classe = classe
            return classe
          })
          .catch((response) => t.sendMessage(
            { alert: 'danger', message: 'Não foi possível recuperar classe selecionada...', time: 5 }))
      })
  }
}
</script>
<style lang="scss">
.arq-doc-item {
  padding: 15px 15px 15px 8px;
  border-bottom: 1px solid #eee;
  margin-left: 7px;
  z-index: 0;
  .inner {
    position: relative;
    .descricao {
      padding: 5px 0;
    }
    .rodape {
      font-size: 80%;
      color: #444;
      display: flex;
      gap: 15px;
    }
    .inner-preview {
      background-color: #777;
      position: absolute;
      display: none;
      top: -15px;
      right: -15px;
      bottom: -15px;
      padding: 10px;
      z-index: 1;
      img {
        position:relative;
        height: 100%;
        width: auto;
      }
      .actions {
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        position: absolute;
        display: none;
        align-items: stretch;
        justify-content: end;
        .previous, .next {
          display: flex;
          flex: 0 0 50%;
          justify-content: left;
          align-items: center;
          text-decoration: none;
          cursor: pointer;
          color: #0003;
          padding: 10px 20px;
          font-size: 150%;
          &:hover {
            color: #09f;
          }
        }
        .next {
          justify-content: right;
        }
      }
    }
  }
  &:hover {
    background-color: #f5f5f5;
    padding: 15px 15px 15px 15px;
    margin-left: 0px;
    .inner-preview {
      display: block;
    }
  }
}
</style>
