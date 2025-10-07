<template>
  <div class="individuo-list">
    <div :class="['individuo-base', 'manager', status_microfone === 0 ? 'muted' : '']" :style="{flex: `0 0 ${100 / (individuos.length + 1)}%`}">
      <div class="inner">
        <div class="controls">
          <button
          class="btn-fone"
          title="Ativar/Desativar Todos os Microfones"
          @click="status_microfone = status_microfone === 0 ? 1 : 0"
        >
          <i :class="status_microfone === 0 ? 'fas fa-2x fa-microphone-slash' : 'fas fa-2x fa-microphone'"></i>
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
      status_microfone: 0,
      default_timer: 300, // segundos
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
    'itens.individuo_list': function (newVal, oldVal) {
      // se todos os individuos estiverem com microfone ativo, seta o status geral como ativo
      if (newVal && Object.keys(newVal).length > 0) {
        // const all_on = Object.values(newVal).every(individuo => individuo.status_microfone === true)
        // setar o status sem disparar o watcher
        this.status_microfone = 1
      } else {
        this.status_microfone = 0
      }
    },
    status_microfone: function (newVal, oldVal) {
      console.log('status_microfone global mudou para', newVal, 'de', oldVal)
      this.individuos.forEach(individuo => {
        if (this.nulls.includes(individuo) || !this.$refs[`individuo-${individuo.id}`] || this.$refs[`individuo-${individuo.id}`].length === 0) {
          return
        }
        if (individuo.microfone_sempre_ativo && newVal === 0) {
          console.log('individuo.microfone_sempre_ativo is true, not allowing to turn off microphone for individuo', individuo.id)
          return
        }
        individuo.status_microfone = newVal === 1
        // Atualiza o status do microfone no componente filho
        this.$refs[`individuo-${individuo.id}`][0].status_microfone = newVal
        // this.$refs[`individuo-${individuo.id}`][0].send_individual_updates = false
      })
      /* this.$nextTick(() => {
        this.utils.getModelAction('painelset', 'evento', this.evento.id, 'toggle_microfones', `&status_microfone=${newVal ? 'on' : 'off'}`)
          .then(response => {
            console.log('toggle_microfones response', response)
          })
          .catch(error => {
            console.error('toggle_microfones error', error)
          })
      }) */
    }
  },
  methods: {
    refreshOldAparteante (individuo_id) {
      console.log('refreshOldAparteante', individuo_id)
      const aparteante = this.itens.individuo_list[individuo_id]
      aparteante.aparteante = null
      aparteante.apartedado = null
      this
        .refreshState({
          app: 'painelset',
          model: 'individuo',
          id: individuo_id,
          value: aparteante
        })
        .then((individuo) => {
          if (individuo) {
            this.$set(this.itens.individuo_list, individuo_id, individuo)
          }
        })
    },
    selectToAparte (individuo_id) {
      console.log('selectToAparte', individuo_id)
      const individuoAparte = this.itens.individuo_list[individuo_id]
      const individuoComPalavra = this.getIndividuoComPalavra
      if (!individuoAparte) {
        return
      }
      if (!individuoComPalavra) {
        return
      }
      if (individuoAparte.id === individuoComPalavra.id) {
        return
      }
      this.$refs[`individuo-${individuoAparte.id}`][0].send_individual_updates = false
      this.$refs[`individuo-${individuoAparte.id}`][0].status_microfone = 1
      this.$refs[`individuo-${individuoAparte.id}`][0].aparteante = !this.$refs[`individuo-${individuoAparte.id}`][0].aparteante
    },
    toggleComAPalavra (individuo_id) {
      // bloquear graficamente clique neste componente até o final do processamento

      console.log(individuo_id, 'toggleComAPalavra', individuo_id)
      this.itens.individuo_list = Object.fromEntries(
        Object.entries(this.itens.individuo_list).map(([key, value]) => [
          key,
          {
            ...value,
            com_a_palavra: value.id === individuo_id ? !value.com_a_palavra : false
          }
        ])
      )
      this.$refs[`individuo-${individuo_id}`][0].status_microfone = (
        this.itens.individuo_list[individuo_id].com_a_palavra
          ? 1 : this.$refs[`individuo-${individuo_id}`][0].status_microfone
      )
    },
    fetch (metadata) {
      if (metadata && metadata.action === 'post_delete' && metadata.model === 'individuo') {
        this.$delete(this.itens['individuo_list'], metadata.id)
        return
      }
      if (metadata === undefined) {
        // Busca a lista completa de Individuos para este Evento
        this
          .fetchModelOrderedList('painelset', 'individuo', 'order', 1, `&evento=${this.evento.id}`,
            (value) => {
              this.refreshState({
                app: 'painelset',
                model: 'individuo',
                id: value.id,
                value: value
              })
            })
        return
      }
      const t = this
      t.refreshState(metadata)
        .then(obj => {
          if (obj.evento === t.evento.id) {
            t.$set(t.itens['individuo_list'], metadata.id, obj)
            t.$nextTick(() => {
              // se todos os individuos estiverem com microfone ativo, seta o status geral como ativo
              if (Object.values(t.itens.individuo_list).every(
                individuo => individuo.status_microfone === true)) {
                t.status_microfone = 1
              }
            })
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
