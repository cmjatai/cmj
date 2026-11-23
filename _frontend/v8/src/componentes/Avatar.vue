<template>
  <AvatarRoot
    class="v8-avatar-base"
    :data-tamanho="tamanho"
  >
    <AvatarImage
      v-if="src"
      class="v8-avatar-base-imagem"
      :src="src"
      :alt="nome"
    />
    <AvatarFallback
      class="v8-avatar-base-iniciais"
      :delay-ms="src ? 300 : undefined"
      :aria-label="nome || undefined"
    >
      {{ iniciais }}
    </AvatarFallback>
  </AvatarRoot>
</template>

<script setup>
// Avatar (docs/specs/v8/componentes.md), sobre o Avatar do Reka UI: a imagem da pessoa e, enquanto
// ela não carrega ou se falhar, as iniciais do nome.
//
//   <Avatar :src="usuario.avatar" :nome="usuario.nome" tamanho="lg" />

// 1. Imports
import { computed } from 'vue'
import { AvatarFallback, AvatarImage, AvatarRoot } from 'reka-ui'

// 3. Props & Emits
const props = defineProps({
  src: {
    type: String,
    default: ''
  },
  nome: {
    type: String,
    default: ''
  },
  // `sm`, `md` ou `lg`.
  tamanho: {
    type: String,
    default: 'md'
  }
})

// 5. Computed Properties
// Primeira letra do primeiro e do último nome.
const iniciais = computed(() => {
  const partes = props.nome.trim().split(/\s+/).filter(Boolean)
  if (!partes.length) {
    return '?'
  }
  const ultima = partes.length > 1 ? partes[partes.length - 1] : ''
  return `${partes[0][0]}${ultima ? ultima[0] : ''}`.toUpperCase()
})
</script>
