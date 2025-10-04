<template>
  <div class="individuo-list">
    <div :class="['individuo-base', 'manager', sound_status === 0 ? 'muted' : '']">
      <div class="inner">
        <div class="inner-individuo">{{ individuos.length }} Canais neste evento.</div>
        <div class="controls">
          <button
          class="btn-fone"
          title="Ativar/Desativar Todos os Microfones"
          @click="sound_status = sound_status === 0 ? 1 : 0"
        >
          <i :class="sound_status === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
        </button>
        </div>
      </div>
    </div>
    <individuo-base
      v-for="individuo in individuos"
      :key="`individuo-${individuo.id}-${individuo.order}`"
      :ref="`individuo-${individuo.id}`"
      :individuo_id="individuo.id"
      :individuo="individuo"
      @individuo-com-a-palavra="individuoComAPalavra($event)"/>
  </div>
</template>
<script>
import IndividuoBase from '../components/individuos/IndividuoBase.vue'
export default {
  name: 'individuo-list',
  props: {
    evento: {
      type: Object,
      required: true
    }
  },
  components: {
    IndividuoBase
  },
  data () {
    return {
      app: ['painelset'],
      model: ['individuo'],
      init: false,
      sound_status: 0,
      itens: {
        individuo_list: {}
      }
    }
  },
  mounted () {
    console.log('IndividuoList mounted', this.evento)
    const t = this
    t.fetch()
  },
  computed: {
    individuos: {
      get () {
        return _.orderBy(this.itens.individuo_list, ['order', 'name'], ['asc', 'asc'])
      }
    }
  },
  watch: {
    'itens.individuo_list': function (newVal, oldVal) {
      // se todos os individuos estiverem com microfone ativo, seta o status geral como ativo
      if (newVal && Object.keys(newVal).length > 0) {
        const all_on = Object.values(newVal).every(individuo => individuo.sound_status === true)
        // setar o status sem disparar o watcher
        this.sound_status = all_on ? 1 : 0
      } else {
        this.sound_status = 0
      }
    },
    sound_status: function (newVal, oldVal) {
      console.log('sound_status mudou', newVal, oldVal)
      this.individuos.forEach(individuo => {
        if (this.nulls.includes(individuo) || !this.$refs[`individuo-${individuo.id}`] || this.$refs[`individuo-${individuo.id}`].length === 0) {
          return
        }
        this.$refs[`individuo-${individuo.id}`][0].sound_status = newVal
        this.$refs[`individuo-${individuo.id}`][0].send_individual_updates = false
      })
      this.$nextTick(() => {
        this.utils.getModelAction('painelset', 'evento', this.evento.id, 'toggle_microfones', `&sound_status=${newVal ? 'on' : 'off'}`)
          .then(response => {
            console.log('toggle_microfones response', response)
          })
          .catch(error => {
            console.error('toggle_microfones error', error)
          })
      })
    }
  },
  methods: {
    individuoComAPalavra (individuo_id) {
      console.log('individuoComAPalavra', individuo_id)
      this.itens.individuo_list = Object.fromEntries(
        Object.entries(this.itens.individuo_list).map(([key, value]) => [
          key,
          {
            ...value,
            com_a_palavra: value.id === individuo_id
          }
        ])
      )
      this.$refs[`individuo-${individuo_id}`][0].sound_status = 1
    },
    fetch (metadata) {
      if (metadata && metadata.action === 'post_delete' && metadata.model === 'individuo') {
        this.$delete(this.itens['individuo_list'], metadata.id)
        return
      }
      if (metadata === undefined) {
        // Busca a lista completa de Individuos para este Evento
        this.fetchModelOrderedList('painelset', 'individuo', 'order', 1, `&evento=${this.evento.id}`)
        return
      }
      const t = this
      t.refreshState(metadata)
        .then(obj => {
          if (obj.evento === t.evento.id) {
            t.$set(t.itens['individuo_list'], metadata.id, obj)
          } else {
            // Se o indivíduo não pertence mais a este evento, remove-o da lista
            t.$delete(t.itens['individuo_list'], metadata.id)
          }
        })
    }
  }
}
</script>
<style lang="scss">
.individuo-list {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  .individuo-base:first-child {
    border-bottom: 2px solid #fff;
    .inner-individuo, .controls {
      font-weight: bold;
      opacity: 1 !important;
    }
    .inner-individuo {
      cursor: default;
      font-size: 1.2em;
    }
  }
}
</style>
