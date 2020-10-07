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
    <norma-simple-modal-view :html_id="'modal-norma'" :modal_norma="modal_norma" :idd="modal_norma"></norma-simple-modal-view>
  </div>
</template>

<script>
import NormaSimpleModalView from '@/__online/components/norma/NormaSimpleModalView'

export default {
  name: 'side-right',
  components: {
    NormaSimpleModalView
  },
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
