<template>
  <form
    :id="idDoFormulario"
    novalidate
    @submit.prevent="submeter"
  >
    <ErrosGerais :mensagens="gerais" />
    <CampoForm
      v-slot="campo"
      rotulo="Nome"
      :erro="erroDe('nome')"
    >
      <input
        :id="campo.id"
        v-model="valores.nome"
        class="v8-entrada"
        type="text"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="E-mail"
      :erro="erroDe('email')"
    >
      <input
        :id="campo.id"
        v-model="valores.email"
        class="v8-entrada"
        type="email"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
  </form>
  <OverlayFooter>
    <button
      type="button"
      class="v8-btn v8-btn-fantasma"
      @click="overlay.dismiss()"
    >
      Cancelar
    </button>
    <button
      type="submit"
      class="v8-btn v8-btn-primario"
      :form="idDoFormulario"
      :disabled="enviando"
    >
      Salvar
    </button>
  </OverlayFooter>
</template>

<script setup>
// Formulário de amostra do modal `form` da vitrine (V8-DS-009). A validação é local e simula a
// resposta de erro do servidor, para mostrar o erro junto ao campo; nada é enviado (V8-DS-044).

// 1. Imports
import { reactive, useId } from 'vue'
import CampoForm from '~@/overlays/CampoForm.vue'
import ErrosGerais from '~@/overlays/ErrosGerais.vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useFormModal } from '~@/overlays/useFormModal'
import { useOverlay } from '~@/overlays/useOverlay'
import { enviarAmostra } from '~@/modules/ds/amostras'

// 2. Composables
const overlay = useOverlay()
const idDoFormulario = useId()

// 4. State & Refs
const valores = reactive({ nome: '', email: '' })
const { gerais, enviando, submeter, erroDe } = useFormModal({ valores, enviar: enviarAmostra })
</script>
