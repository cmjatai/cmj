<template>
  <div class="w-100 inner inner-sideright">
    <div class="menu">
      <ul>
        <li>
          <b-img @click="toogleNormaDestaque" src="@/assets/img/icon_normas_juridicas_destaque.png" fluid rounded="0" />
          <ul class="list-group">
            <li class="list-group-item"  v-for="item in itensNormasDeDestaque" :key="`srmd${item.id}`"><a href="#">{{item.apelido}}</a></li>
          </ul>
        </li>
      </ul>

      <!--b-img src="@/assets/img/icon_mesa_diretora.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_comissoes.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_parlamentares.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_pautas.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_plenarias.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_materia_legislativa.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_normas_juridicas.png" fluid rounded="0" />
      <b-img src="@/assets/img/icon_relatorios.png" fluid rounded="0" /-->
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
<<<<<<< HEAD
.inner-sideright .menu {
  //display: none;
  a {
    padding: 0.5rem 1rem;
    white-space: nowrap;
    display: block;
    text-decoration: none;
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

=======
.inner-sideright {
  //display: none;
  & > ul {
    padding: 0;
    margin: 0;
    list-style-type: none;
    & >li {
      position: relative;
    }
  }
  ul {
    &.isr-hover {
      position: absolute;
      right: 90%;
      top: 50%;
      display: none;
      &.show {
        display: flex;
      }
      a {
        white-space: nowrap;
      }
    }
  }
>>>>>>> 15a0e01... altera sideright para inserção de itens e subitens
  img {
    padding: 15px;
    cursor: pointer;

  }
}
</style>
