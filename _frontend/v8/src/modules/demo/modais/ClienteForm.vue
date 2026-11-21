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
        maxlength="80"
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
        maxlength="120"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="Cidade"
      :erro="erroDe('cidade')"
    >
      <input
        :id="campo.id"
        v-model="valores.cidade"
        class="v8-entrada"
        type="text"
        maxlength="60"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="Situação"
      :erro="erroDe('situacao')"
    >
      <select
        :id="campo.id"
        v-model="valores.situacao"
        class="v8-entrada"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
        <option
          v-for="situacao in SITUACOES"
          :key="situacao.valor"
          :value="situacao.valor"
        >
          {{ situacao.rotulo }}
        </option>
      </select>
    </CampoForm>
    <CampoForm
      v-slot="campo"
      rotulo="Motivo da inativação"
      :erro="erroDe('motivo')"
    >
      <input
        :id="campo.id"
        v-model="valores.motivo"
        class="v8-entrada"
        type="text"
        maxlength="200"
        autocomplete="off"
        :aria-invalid="campo.invalido"
        :aria-describedby="campo.descritoPor"
      >
    </CampoForm>
  </form>
  <OverlayFooter>
    <button
      type="button"
      class="v8-btn"
      :disabled="enviando"
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
      {{ enviando ? 'Salvando…' : 'Salvar' }}
    </button>
  </OverlayFooter>
</template>
<script setup>
// Formulário de edição do cliente, conteúdo do modal `form` (V8-DEMO-022).
//
// O formulário não tem validação do navegador (`novalidate`): quem valida é o servidor, e é o
// erro dele que aparece junto ao campo ou no topo do modal. Editar um campo marca o modal como
// alterado, e por isso "Cancelar" usa dismiss(), que pede confirmação antes de descartar.
//
// O rodapé do overlay fica fora do <form>. O botão "Salvar" alcança o formulário pelo atributo
// `form`, que aponta para o id dele.

// 1. Imports
import { reactive, useId } from 'vue'
import CampoForm from '~@/overlays/CampoForm.vue'
import ErrosGerais from '~@/overlays/ErrosGerais.vue'
import OverlayFooter from '~@/overlays/OverlayFooter.vue'
import { useFormModal } from '~@/overlays/useFormModal'
import { useOverlay } from '~@/overlays/useOverlay'
import { salvar } from '~@/modules/demo/api'
import { SITUACOES } from '~@/modules/demo/formatos'

// 2. Composables
const overlay = useOverlay()
const idDoFormulario = useId()

// 3. Props & Emits
const props = defineProps({
  cliente: {
    type: Object,
    required: true
  }
})

// 4. State & Refs
const valores = reactive({
  nome: props.cliente.nome || '',
  email: props.cliente.email || '',
  cidade: props.cliente.cidade || '',
  situacao: props.cliente.situacao || 'ativo',
  motivo: props.cliente.motivo || ''
})
const { gerais, enviando, submeter, erroDe } = useFormModal({
  valores,
  enviar: dados => salvar(props.cliente.id, dados)
})

// 5. Computed Properties
// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
</script>
