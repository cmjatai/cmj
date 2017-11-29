<template lang="html">
  <div>
    <span>{{message}}</span>
  </div>
</template>

<script>
import { DocumentoResource } from '../../../resources'
export default {
  name: 'documento-edit',
  data() {
    return {
      documentoResource: DocumentoResource,
      message: ''
    }
  },

  mounted: function() {
      let id = this.$route.params.id;
      this.documentoResource.getDocumento(id)
        .then( (req) => {
          this.message = req.data.titulo
        })
        .catch( (e) => {
          this.message = 'erro erro erro'
        });



  }

}
</script>

<style lang="scss">
</style>
