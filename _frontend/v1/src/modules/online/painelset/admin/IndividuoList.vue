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
      :key="`individuo-${individuo.id}`"
      :ref="`individuo-${individuo.id}`"
      :individuo_id="individuo.id"
      :individuo="individuo"/>
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
    t.fetchModelOrderedList('painelset', 'individuo', 'order')
  },
  computed: {
    individuos: function () {
      return _.orderBy(
        this.itens.individuo_list,
        ['order', 'name'],
        ['asc', 'asc']
      )
    }
  },
  watch: {
    sound_status: function (newVal, oldVal) {
      console.log('sound_status mudou', newVal, oldVal)
      this.individuos.forEach(individuo => {
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
