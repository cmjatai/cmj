<template>
  <div class="card-group">
    <div class="card" v-for="(item, key) in sessoes" :key="key">
      <div class="card-img-top">
        <div v-if="item.url_video" class="embed-responsive embed-responsive-16by9">
          <iframe :id="`ytplayer${key}`" type="text/html" allowfullscreen
            :src="`https://www.youtube.com/embed${ url_video_split(item.url_video) }`"
            frameborder="0"></iframe>
        </div>
      </div>
      <div class="card-body">
        <div class="card-title">
          <a :href="item.link_detail_backend">{{item.__str__}}</a>
        </div>
        <div class="card-text">
          <strong v-if="item.upload_ata">
            <a :href="item.upload_ata">
            <i class="fas fa-file-pdf"></i>

              Ata da Sessão</a>
          </strong>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import ActionLink from './ActionLink'
export default {
  name: 'action-link-sessaoplenaria',
  props: ['app', 'model', 'params'],
  extends: {
    ...ActionLink
  },
  computed: {
    sessoes: function () {
      let ss = this.values.slice(4, 7)
      return ss
    }
  },
  methods: {
    data_sessao (data_inicio) {
      try {
        const data = this.stringToDate(data_inicio, 'yyyy-mm-dd', '-')
        return `${data.getDate()}/${data.getMonth() + 1}/${data.getFullYear()}`
      } catch (Exception) {
        return ''
      }
    },
    url_video_split: function (url) {
      const urlObject = new URL(url)
      const urlParams = new URLSearchParams(urlObject.search)
      return `${urlParams.get('v') || urlObject.pathname}/?start=${urlParams.get('t') || 0}`
    }
  }
}
</script>
<style lang="scss" scoped>
.card-group {
  & > .card {
    flex: 1 1 33%;
    border: 0;
    padding: 0 10px 10px 10px;
  }
}
</style>
