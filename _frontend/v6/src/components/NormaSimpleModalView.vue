<template>
  <div
    :id="htmlId"
    class="modal norma-simple-modal-view fade show"
    tabindex="-1"
  >
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <span v-html="props.normaObject.apelido" /><br>
            <small v-html="props.normaObject.__str__" />
          </h5>
          <a
            class="btn btn-success btn-open-external"
            :href="`/norma/${props.normaObject.id}/ta`"
            target="_blank"
            rel="noopener noreferrer"
            title="Abrir texto consolidado em nova aba"
          >
            <FontAwesomeIcon
              :icon="['fas', 'external-link-alt']"
            />
          </a>
          <button
            type="button"
            class="btn-close"
            @click="emit('close')"
          />
        </div>
        <div
          v-if="normaRender"
          class="modal-body"
          v-html="normaRender"
        />
        <div
          v-else
          class="modal-body"
        >
          Carregando texto...
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            @click="emit('close')"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { useSyncStore } from '~@/stores/SyncStore'
import { ref, onMounted, computed, nextTick } from 'vue'
import axios from 'axios'

const emit = defineEmits(['close'])

const syncStore = useSyncStore()

const props = defineProps({
  htmlId: {
    type: String,
    required: true
  },
  normaObject: {
    type: Object,
    required: true
  }
})

const normaRender = ref(null)

onMounted(() => {
  syncStore.fetchSync({
    app: 'norma',
    model: 'normajuridica',
    id: props.normaObject.id,
    params: {},
    force_fetch: false
  }).then(() => {

    axios.get(
      `/norma/${props.normaObject.id}/ta?embedded`
    ).then((res) => {
      normaRender.value = res.data
      nextTick(() => {
        const links = document.querySelectorAll(
          '.cp a:not([target="_blank"])'
        )
        links.forEach((link) => {
          link.setAttribute('target', '_blank')
          link.setAttribute('rel', 'noopener noreferrer')
        })
      })
    })

  })
})

</script>

<style lang="scss">

.norma-simple-modal-view {
  background-color: #000b;
  z-index: 10000;
  display: block;

  .modal-header {
    gap: 1em;
  }

  .cp {
    line-height: 1.5em;

    .cp-linha-vigencias,
    .vigencia-active,
    .dptt .dne,
    .btns-action,
    .btn-group,
    .tipo-vigencias {
      display: none !important;
    }

    a {
      text-decoration: none !important;
      //cursor: default;
    }
  }
}

@media screen and (max-width: 480px) {}
</style>
