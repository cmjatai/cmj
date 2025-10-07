<template>
  <div class="individuo-list">
    <div :class="['individuo-base', 'manager',
      status_microfone ? '' : 'muted']" :style="{flex: `0 0 ${100 / (individuos.length + 1)}%`}">
      <div class="inner">
        <div class="controls">
          <button
          class="btn-fone"
          title="Ativar/Desativar Todos os Microfones"
          @click="toggleAllMicrofones()"
        >
          <i :class="status_microfone ? 'fas fa-2x fa-microphone' : 'fas fa-2x fa-microphone-slash'"></i>
        </button>
        </div>
        <div class="inner-individuo py-2">{{ individuos.length }} CANAIS NESTE EVENTO</div>
        <div class="inner-individuo">
          <div class="default-timer">
            <button class="btn btn-link">
              <i class="fas fa-2x fa-arrow-down" @click="default_timer > 60 ? default_timer -= 60 : default_timer = 60"></i>
            </button>
            Tempo Padrão: {{ (default_timer / 60).toFixed(0) }} min
            <button class="btn btn-link">
              <i class="fas fa-2x fa-arrow-up" @click="default_timer < 600 ? default_timer += 60 : default_timer = 600"></i>
            </button>
          </div>
        </div>
        <div class="inner-individuo">
          <input
            type="checkbox"
            id="pause_parent_on_aparte"
            v-model="pause_parent_on_aparte"
            title="Pausar o Cronômetro de quem está com a palavra quando alguém solicitar aparte"
          />
        </div>
      </div>
    </div>
    <individuo-base :style="{flex: `0 0 ${100 / (individuos.length + 1)}%`}"
      v-for="individuo in individuos"
      :key="`individuo-${individuo.id}-${individuo.order}`"
      :ref="`individuo-${individuo.id}`"
      :individuo_id="individuo.id"
      :individuo="individuo"
      :default_timer="default_timer"
      @toggle-com-a-palavra="toggleComAPalavra($event)"
      @select-to-aparte="selectToAparte($event)"
      @refreshOldAparteante="refreshOldAparteante($event)"
    />
  </div>
</template>
<script>
import IndividuoBase from '../components/individuos/IndividuoBase.vue'
import Vuex from 'vuex'
export default {
  name: 'individuo-list',
  props: {
    evento: {
      type: Object,
      required: true
    },
    pause_parent_on_start: {
      type: Boolean,
      required: false,
      default: false
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
      status_microfone: false,
      pause_parent_on_aparte: this.pause_parent_on_start,
      default_timer: 300, // segundos
      itens: {
        individuo_list: {}
      }
    }
  },
  computed: {
    ...Vuex.mapGetters([
      'getIndividuoComPalavra'
    ]),
    individuos: {
      get () {
        return _.orderBy(this.itens.individuo_list, ['order', 'name'], ['asc', 'asc'])
      }
    }
  },
  watch: {
    init: function (newVal, oldVal) {
      // verifica se todos indivíduos estão com microfone ligado
      let all_on = Object.values(this.itens.individuo_list).every(
        individuo => individuo.status_microfone === true)
      this.status_microfone = all_on
    },
    pause_parent_on_start: function (newVal, oldVal) {
      this.pause_parent_on_aparte = newVal
    },
    pause_parent_on_aparte: function (newVal, oldVal) {
      const t = this
      const query_params = [
        `pause_parent_on_aparte=${newVal ? 'on' : 'off'}`
      ]
      t
        .utils.getModelAction(
          'painelset', 'evento', this.evento.id, 'pause_parent_on_aparte',
          query_params.join('&')
        )
        .then(response => {
          console.log(this.evento, 'pause_parent_on_aparte', response)
        })
        .catch(error => {
          console.error(this.evento.id, 'pause_parent_on_aparte', error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar Configurar Pausa: ' + error.response.data, time: 5 })
        })
    }
  },
  mounted () {
    console.log('IndividuoList mounted', this.evento)
    const t = this
    t.fetch()
  },
  methods: {
    toggleAllMicrofones () {
      const t = this
      t.status_microfone = !t.status_microfone
      const query_params = [
        `status_microfone=${t.status_microfone ? 'on' : 'off'}`
      ]
      t
        .utils.getModelAction(
          'painelset', 'evento', this.evento.id, 'toggle_microfones',
          query_params.join('&')
        )
        .then(response => {
          console.log(this.evento, 'toggle_microfones', response)
        })
        .catch(error => {
          console.error(this.evento.id, 'toggle_microfones', error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar Microfones: ' + error.response.data, time: 5 })
        })
    },
    fetch (metadata) {
      const t = this
      if (metadata && metadata.action === 'post_delete' && metadata.model === 'individuo') {
        t.$delete(this.itens['individuo_list'], metadata.id)
        return
      }
      if (metadata === undefined) {
        // Busca a lista completa de Individuos para este Evento
        t
          .fetchModelOrderedList('painelset', 'individuo', 'order', 1, `&evento=${this.evento.id}`,
            (value) => {
              t.refreshState({
                app: 'painelset',
                model: 'individuo',
                id: value.id,
                value: value
              })
            })
          .then(list => {
            setTimeout(() => {
              t.init = true
              t.$emit('onload')
            }, 500)
          })
        return
      }
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
  height: 100%;
  justify-content: stretch;
  position:absolute;
  top:0;
  left:0;
  right:0;
  bottom:0;
  overflow: hidden;
  .individuo-base:first-child {
    border-bottom: 1px solid #fff;
    font-size: 0.7em;
    .inner-individuo, .controls {
      border-right: 0;
      font-weight: bold;
      opacity: 1 !important;
      text-align: center;
    }
    .inner-individuo {
      border-left: 1px solid white;
      cursor: default;
      justify-content: center;
      font-size: 1.2em;
      .default-timer {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        gap: 0.5em;
        .btn {
          padding: 0 0.5em;
          color: #0004;
          text-decoration: none;
          &:hover {
            color: #000;
          }
        }
      }
    }
  }
}
</style>
