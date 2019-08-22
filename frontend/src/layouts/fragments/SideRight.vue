<template>
  <div class="w-100 inner inner-sideright">
    <div class="menu">
      <ul>
        <li>
          <b-img @click="toogleNormaDestaque" src="@/assets/img/icon_normas_juridicas_destaque.png" fluid rounded="0" />
          <ul class="list-group">
            <li class="list-group-item" v-for="item in itensNormasDeDestaque" :key="`srmd${item.id}`">
              <a :href="`/sapl/ta/${item.id}/text`" target="_blank">
                  {{item.apelido}}
              </a>
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
    'modal_norma': function (nv, ov) {
      const t = this
      $.ajax({
        url: `http://10.42.0.1:9000/sapl/ta/${nv.id}/text?embedded`,
        type: 'GET',
        success: function (res) {
          var text = res
          t.$set(nv, 'html', text)
        }
      })
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
      this.fetchModelListAction('norma', 'normajuridica', 'destaques', 1)
    }, 1000)
  },
  methods: {
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
          t.$set(t.itens[`${metadata.model}_list`], metadata.id, obj)
        })
    }
  }
}
</script>

<style lang="scss">
.modal-cmj {
  background-color: #000b;
}
.inner-sideright .menu {
  // display: none;
  a {
    padding: 0.5rem 1rem;
    white-space: nowrap;
    display: block;
    text-decoration: none;
    width: 100%;
    border-radius: 0px;
    text-align: center;
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
</style>
