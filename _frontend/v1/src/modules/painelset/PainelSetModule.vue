<template>
  <div class="painelset-module">
    <div v-if="$route.name === 'painelset_list_link'" class="painelset-module-header">
      <ul class="p-2">
        <li v-for="evento in itensEventos" :key="evento.id">
          <a :href="evento.link_detail_backend" target="_blank">
            {{ evento.id }} - {{ evento.name }}<br>
            Data e Hora Prevista: {{ evento.start_previsto }}<br>
            Duração: {{ evento.duration }}
            <span v-if="evento.start_real">Iniciado em: {{ evento.start_real }} </span>
            <span v-if="evento.end_real"> - Finalizado em: {{ evento.end_real }} </span>
          </a>
          &nbsp;
          <a href="#" @click.prevent="play(evento)"><i class="fas fa-play"></i></a>
        </li>
      </ul>
    </div>
    <router-view></router-view>
  </div>
</template>

<script>
import Vuex from 'vuex'
export default {
  name: 'painelset-module',
  data () {
    return {
      itens: {
        evento_list: {}
      }
    }
  },
  computed: {
    itensEventos: {
      get () {
        return _.orderBy(this.itens.evento_list, ['start_real', 'start_previsto'], ['desc', 'desc'])
      }
    }
  },
  mounted: function () {
    const t = this
    t.setSideleftVisivel(true)
    t.setSiderightVisivel(false)
    t.fetchModelOrderedList('painelset', 'evento', '-start_real,-start_previsto')
  },
  methods: {
    ...Vuex.mapActions([
      'setSideleftVisivel',
      'setSiderightVisivel'
    ]),
    play (eventoId) {
      if (eventoId) {
        this.$router.push({ name: 'painelset_admin_link', params: { id: eventoId.id } })
      }
    }
  }
}
</script>

<style lang="scss">
</style>
