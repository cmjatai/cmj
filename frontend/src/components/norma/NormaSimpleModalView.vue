<template>
  <div :class="['norma-simple-modal-view', 'modal', 'fade']"  :id="html_id" >
    <div class="modal-dialog modal-xl" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="#titulo" v-if="norma_render" >
            {{norma_render.apelido !== '' ? norma_render.apelido : ''}} ({{norma_render.__str__}})
            </h5>
          <button type="button" class="close" data-dismiss="modal" aria-label="Fechar">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="norma_render && !norma_render.html">Carregando texto...</div>
          <div v-if="norma_render" v-html="norma_render.html"></div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-dismiss="modal">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import '@/__apps/compilacao/main'
export default {
  name: 'norma-simple-modal-view',
  props: ['html_id', 'modal_norma', 'idd'],
  data () {
    return {
      app: ['norma'],
      model: ['normajuridica'],
      norma_render: null
    }
  },
  watch: {
    'modal_norma': function (nv, od) {
      if (nv !== null) {
        this.norma_render = nv
      }
    },
    'norma_render': function (nv, ov) {
      if (nv !== null && nv.html === undefined) {
        this.getText(nv)
      }
    },
    'idd': function (nv, ov) {
      const t = this
      if (nv !== null) {
        t.utils
          .getModel('norma', 'normajuridica', t.idd)
          .then(response => {
            t.norma_render = response.data
          })
      }
    }

  },
  computed: {
  },
  mounted () {
    const t = this
    t.$nextTick()
      .then(() => {
        if (t.idd != null && typeof t.idd === 'number') {
          t.getObject({
            app: 'norma',
            model: 'normajuridica',
            id: t.idd
          }).then(obj => {
            t.norma_render = obj
          })
        }
      })
  },
  methods: {
    getText (nv) {
      let t = this
      if (nv.id !== undefined && nv.id > 0) {
        $.ajax({
          url: `/sapl/norma/${nv.id}/ta?embedded`,
          type: 'GET',
          success: function (res) {
            var text = res
            t.$set(nv, 'html', text)
          }
        })
      }
    },
    fetch (metadata) {
      const t = this
      if (t.modal_norma !== undefined && t.modal_norma.id === metadata.id && metadata.model === t.model[0]) {
        this.refresh()
      }
    },
    refresh (metadata) {
      const t = this
      t.getObject(metadata)
        .then(obj => {
          if (obj.norma_de_destaque) {
            t.$set(t.itens[`${metadata.model}_list`], metadata.id, obj)
            // t.getText(obj)
          }
        })
    }
  }
}
</script>

<style lang="scss">

.norma-simple-modal-view {
  background-color: #000b;
  .cp {
     font-size: 1.2em;
     line-height: 1.5em;
     .cp-linha-vigencias,
     .vigencia-active,
     .dptt .dne,
     .btns-action,
     .btn-group,
     .nota-alteracao,
     .tipo-vigencias{
       display: none !important;
     }
     a {
       text-decoration: none !important;
       pointer-events: none;
       cursor: default;
     }
  }
}
@media screen and (max-width: 480px) {
}
</style>
