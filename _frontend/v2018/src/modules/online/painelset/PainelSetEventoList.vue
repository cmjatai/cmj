<template>
  <div class="painelset-evento-list">
    <div class="header">
      <h1>Eventos</h1>
    </div>
    <div class="container">
      <painel-set-evento-list-item
        v-for="evento in eventos"
        :key="`evento-${evento.id}`"
        :evento="evento"
      />
    </div>
    <router-view></router-view>
  </div>
</template>

<script>

export default {
  name: 'painelset-evento-list',
  components: {
    'painel-set-evento-list-item': () => import('./PainelSetEventoListItem.vue')
  },
  data () {
    return {
    }
  },
  computed: {
    eventos: {
      get () {
        if (this.data_cache?.painelset_evento) {
          return _.orderBy(Object.values(this.data_cache.painelset_evento), ['start_real', 'start_previsto'], ['desc', 'desc'])
        }
        return []
      }
    }
  },
  mounted: function () {
    const t = this
    t.fetchSync({
      app: 'painelset',
      model: 'evento',
      params: { o: '-start_real,-start_previsto' }
    })
  }
}
</script>

<style lang="scss">
.painelset-evento-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: auto;
  user-select: none;

  .header {
    background: white;
    padding: 10px 20px;
    h1 {
      margin: 0;
      font-weight: 600;
    }
  }

  .container {
    margin-top: 20px;
  }

  .row {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 10px;
  }

  .col-auto {
    display: flex;
    align-items: center;
    justify-content: center;
    .btn {
      font-size: 1em;
    }

  }
}
</style>
