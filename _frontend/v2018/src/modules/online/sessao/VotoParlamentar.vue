<template>
  <div :class="['voto-parlamentar']">
    <div class="inner-voto">
      <a href="#" class="btn btn-lg btn-success" @click="sendVoto('Sim')">SIM</a>
      <a href="#" class="btn btn-lg btn-danger" @click="sendVoto('Não')">NÃO</a>
      <a href="#" class="btn btn-lg btn-warning" @click="sendVoto('Abstenção')">Abstenção</a>
    </div>
    <div class="voto-result">
      <div v-if="voto">
        Voto Computado: <strong>{{ voto.voto }}</strong>
      </div>
      <div v-else>
        Voto não Computado
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'voto-parlamentar',
  props: ['item', 'type'],
  components: {
  },
  data () {
    return {
      app: ['sessao'],
      model: ['votoparlamentar'],
      itens: {
        votoparlamentar_list: {}
      }
    }
  },
  watch: {
  },
  computed: {
    voto () {
      const t = this
      const field = t.type === 'ordemdia' ? 'ordem' : 'expediente'
      const votos = Object.values(t.itens.votoparlamentar_list).filter(
        v => v.parlamentar === t.user.votante.parlamentar_id && v[field] === t.item.id
      )
      return votos.length > 0 ? votos[0] : null
    }
  },
  mounted () {
    this.refresh()
  },
  methods: {
    refresh () {
      const t = this
      t.fetchModelOrderedList(
        'sessao',
        'votoparlamentar',
        '',
        1,
        '&' + (t.type === 'ordemdia' ? 'ordem' : 'expediente') + '=' + t.item.id
      )
    },
    fetch (metadata) {
      if (metadata.action === 'post_delete') {
        this.$delete(this.itens[`${metadata.model}_list`], metadata.id)
        return
      }
      if (metadata.app === 'sessao' && metadata.model === 'votoparlamentar') {
        const t = this
        t.getObject(metadata)
          .then(obj => {
            if (obj.ordem === t.item.id || obj.expediente === t.item.id) {
              t.$set(t.itens[`${metadata.model}_list`], metadata.id, obj)
            }
          })
      }
    },
    sendVoto (voto) {
      const t = this
      const field = t.type === 'ordemdia' ? 'ordem' : 'expediente'
      const form = {
        parlamentar: t.user.votante.parlamentar_id,
        voto: voto,
        user: t.user.id,
        [field]: t.item.id
      }
      if (t.voto) {
        this.utils.patchModel('sessao', 'votoparlamentar', t.voto.id, form)
          .then((response) => {
            console.debug(response.data)
          }).catch((error) => {
            console.debug(error)
          })
      } else {
        this.utils.postModel('sessao', 'votoparlamentar', form)
          .then((response) => {
            console.debug(response.data)
          }).catch((error) => {
            console.debug(error)
          })
      }
    }
  }
}
</script>

<style lang="scss">
.voto-parlamentar {
  position: absolute;
  top: 0em;
  right: 0em;
  left: 0;
  bottom: 0;
  display: flex;
  background-color: #000d;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  zoom: 2;
  z-index: 1;
  .inner-voto {
    display: flex;
    gap: 2em;
  }
  .voto-result {
    margin-top: 1em;
    color: #fff;
    font-size: 1.2em;
    background-color: #000A;
    padding: 0.5em 1em;
    border-radius: 0.5em;
  }
  .btn {
    padding: 1em;
    line-height: 0;
    box-shadow: 0.5em 0.5em 1em #000;
    font-family: 'Graduate', 'Courier New', Courier, monospace;
    font-weight: bold;
    &:hover {
      box-shadow: 0.5em 0.5em 1em #222;
    }
  }
}

@media screen and (max-width: 991.98px) {
  .voto-parlamentar {
    zoom: 1.7;
  }
}
@media screen and (max-width: 800px) {
  .voto-parlamentar {
    zoom: 1.5;
  }
}
@media screen and (max-width: 600px) {
  .voto-parlamentar {
    zoom: 1;
  }
}
@media screen and (max-width: 480px) {
  .voto-parlamentar {
    zoom: 1;
    .inner-voto {
      gap: 1em;
    }
    .btn {
      padding: 1em 0.7em;
    }
  }
}
</style>
