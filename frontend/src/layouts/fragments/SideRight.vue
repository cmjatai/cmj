<template>
  <div class="w-100 inner inner-sideright">
    <div class="menu">
      <ul>
        <li>
          <b-img @click="toogleNormaDestaque" src="@/assets/img/icon_normas_juridicas_destaque.png" fluid rounded="0" />
          <ul class="list-group">
            <li class="list-group-item" v-for="item in itensNormasDeDestaque" :key="`srmd${item.id}`">
              <button
                type="button"
                class="btn btn-secondary"
                data-toggle="modal"
                data-target="#modal-norma"
                @click="modal_norma=item">
                  {{item.apelido}}
              </button>
            </li>
          </ul>
        </li>
      </ul>
    </div>
    <div v-if="modal_norma" class="modal fade modal-cmj" id="modal-norma" tabindex="-1" role="dialog" aria-labelledby="ModalNorma" aria-hidden="true">
      <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="#titulo">{{modal_norma.apelido}}</h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Fechar">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body" v-html="modal_norma.html">
            Carregando...
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Fechar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import '@/__apps/compilacao/main'
export default {
  name: 'side-right',
  data () {
    return {
      app: ['norma'],
      model: ['normajuridica'],
      menu_norma_destaque: false,
      modal_norma: null,
      itens: {
        normajuridica_list: {}
      }
    }
  },
  watch: {
    /* 'modal_norma': function (nv, ov) {
      const t = this

    } */
    'itens.normajuridica_list': function (nv, ov) {
      let t = this
      setTimeout(() => {
        _.mapKeys(nv, function (value, key) {
          t.getText(value)
        })
      }, 10000)
    }
  },
  computed: {
    itensNormasDeDestaque: {
      get () {
        return _.orderBy(this.itens.normajuridica_list, 'apelido')
      }
    }
  },
  mounted () {
    setTimeout(() => {
      this.fetchModelListAction('norma', 'normajuridica', 'destaques', 1, null)
    }, 2000)
  },
  methods: {
    getText (nv) {
      let t = this
      if (nv.id !== undefined && nv.id > 0) {
        $.ajax({
          url: `/sapl/ta/${nv.id}/text?embedded`,
          type: 'GET',
          success: function (res) {
            var text = res
            t.$set(nv, 'html', text)
          }
        })
      }
    },
    toogleNormaDestaque (event) {
      this.menu_norma_destaque = !this.menu_norma_destaque
    },

    fetchItens (model_list = this.model) {
      const t = this
      _.mapKeys(model_list, function (value, key) {
        _.mapKeys(t.itens[`${value}_list`], function (obj, k) {
          obj.vue_validate = false
        })
        t.$nextTick()
          .then(function () {
            this.fetchModelListAction('norma', 'normajuridica', 'destaques', 1)
          })
      })
    },

    fetch (metadata) {
      if (metadata.action === 'post_delete') {
        this.$delete(this.itens[`${metadata.model}_list`], metadata.id)
        return
      }

      const t = this
      t.getObject(metadata)
        .then(obj => {
          if (obj.norma_de_destaque) {
            t.$set(t.itens[`${metadata.model}_list`], metadata.id, obj)
            // t.getText(obj)
          }
        })
    }
  }
}
</script>

<style lang="scss">
.modal-cmj {
  background-color: #000b;
  .cp {
     font-size: 1.2em;
     line-height: 1.5em;
     .cp-linha-vigencias,
     .vigencia-active,
     .dptt .dne,
     .btns-action,
     .btn-group,
     .nota-alteracao,
     .tipo-vigencias{
       display: none !important;
     }
  }
}
.inner-sideright .menu {
  // display: none;
  button {
    padding: 0.5rem 1rem;
    white-space: nowrap;
    display: block;
    text-decoration: none;
    width: 100%;
    border-radius: 0px;
    text-align: left;
  }
  ul {
    padding: 0;
    margin: 0;
    list-style-type: none;
    ul {
     display: none;
    }
    li {
      position: relative;
      padding: 0;
      &:hover {
        background-color:  #ddd;
        ul {
          display: flex;
          position: absolute;
          right: 80%;
          top: 50%;
        }
      }
    }
  }

  img {
    padding: 15px;
    cursor: pointer;
  }
}

@media screen and (max-width: 800px){
  .inner-sideright .menu {
    img {
      padding: 5px;
    }
  }
}

</style>
