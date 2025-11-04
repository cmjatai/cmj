<template>
  <div class="individuo-list">
    <div :class="['individuo-base', 'manager',
      status_microfone ? '' : 'muted']">
      <div class="inner">
        <div class="controls">
          <button
          class="btn-action btn-fone"
          title="Ativar/Desativar Todos os Microfones"
          @click="toggleAllMicrofones()"
        >
          <i :class="status_microfone ? 'fas fa-2x fa-microphone' : 'fas fa-2x fa-microphone-slash'"></i>
        </button>
        </div>
        <div class="inner-individuo py-2">{{ individuos.length }} CANAIS</div>
        <div class="inner-individuo">
          <div class="default-timer">
            <button class="btn btn-link">
              <i class="fas fa-arrow-down" @click="default_timer > 60 ? default_timer -= 60 : default_timer = 60"></i>
            </button>
            Tempo Padrão: {{ (default_timer / 60).toFixed(0) }} min
            <button class="btn btn-link">
              <i class="fas fa-arrow-up" @click="default_timer < 600 ? default_timer += 60 : default_timer = 600"></i>
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
    <div class="individuos">
      <individuo-base
      v-for="individuo in individuos"
      :key="`individuo-${individuo.id}-${individuo.order}`"
      :ref="`individuo-${individuo.id}`"
      :individuo_id="individuo.id"
      :default_timer="default_timer"
      />
    </div>
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
      init: false,
      status_microfone: false,
      pause_parent_on_aparte: this.pause_parent_on_start,
      default_timer: 300 // segundos
    }
  },
  computed: {
    individuos: {
      get () {
        if (this.data_cache?.painelset_individuo) {
          return _.orderBy(
            _.filter(
              Object.values(this.data_cache.painelset_individuo),
              { evento: this.evento.id }
            ),
            ['order'],
            ['asc']
          )
        }
        return []
      }
    },
    cronometros () {
      if (this.data_cache?.painelset_individuo) {
        const cronometros = []
        for (const individuo of Object.values(this.data_cache.painelset_individuo)) {
          if (individuo.evento === this.evento.id && individuo.cronometro) {
            cronometros.push(this.data_cache.painelset_cronometro[individuo.cronometro])
          }
        }
        return cronometros
      }
      return []
    }
  },
  watch: {
    individuos: {
      handler (newVal, oldVal) {
        // verifica se todos indivíduos estão com microfone ligado
        this.status_microfone = this.individuos.every(
          individuo => individuo.status_microfone === true)
      },
      deep: true
    },
    pause_parent_on_start: function (newVal, oldVal) {
      this.pause_parent_on_aparte = newVal
    },
    pause_parent_on_aparte: function (newVal, oldVal) {
      const t = this
      if (t.cronometros && t.cronometros.length > 0) {
        if (t.cronometros[0] && t.cronometros[0].pause_parent_on_start === newVal) {
          return
        }
      }
      const query_params = {
        pause_parent_on_aparte: newVal ? 'on' : 'off'
      }
      t
        .utils.patchModelAction(
          'painelset', 'evento', this.evento.id, 'pause_parent_on_aparte',
          query_params
        )
        .then(response => {
          console.debug(this.evento, 'pause_parent_on_aparte', response)
        })
        .catch(error => {
          console.error(this.evento.id, 'pause_parent_on_aparte', error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar Configurar Pausa: ' + error.response.data, time: 5 })
        })
    }
  },
  mounted () {
    console.debug('IndividuoList mounted', this.evento)
    this.fetchSync({
      app: 'painelset',
      model: 'individuo',
      params: { evento: this.evento.id }
    })
  },
  methods: {
    toggleAllMicrofones (inclui_microfone_sempre_ativo = true) {
      const t = this
      t.status_microfone = !t.status_microfone
      const query_params = {
        status_microfone: t.status_microfone ? 'on' : 'off',
        inclui_microfone_sempre_ativo: inclui_microfone_sempre_ativo ? 'on' : 'off'
      }
      t
        .utils.patchModelAction(
          'painelset', 'evento', this.evento.id, 'toggle_microfones',
          query_params
        )
        .then(response => {
          console.debug(this.evento, 'toggle_microfones', response)
        })
        .catch(error => {
          console.error(this.evento.id, 'toggle_microfones', error)
          this.sendMessage({ alert: 'error', message: 'Erro ao atualizar Microfones: ' + error.response.data, time: 5 })
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
  width: 41.6667%;
  justify-content: stretch;
  position:absolute;
  top:0;
  left:0;
  bottom:0;
  overflow: hidden;
  .individuos {
    position: absolute;
    display: flex;
    flex-direction: row;
    //justify-content: space-between;
    top: 2.1em;
    bottom: 0;
    width: 100%;
    flex-wrap: wrap;
    .individuo-base {
      flex: 0 0 100%;
    }
  }
  .individuo-base.manager {
    flex: 0 0 3em;
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
@media screen and (max-width: 991.98px) {
  .individuo-list {
    width: 100%;
    overflow: visible;
    background-color: #222;
    .individuo-base {
      &.manager {
        position: static;
        height: 3em;
        z-index: 1;
        .inner {
          position: absolute;
          overflow: visible;
          top: 0;
          left: 0;
          right: 0;
          height: 3em;
          width: calc(100vw - 48px);
          z-index: 0;
        }
      }
    }
  }
}
</style>
