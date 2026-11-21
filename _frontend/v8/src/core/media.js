import { onBeforeUnmount, ref } from 'vue'

// Largura de corte entre tela estreita e larga: a mesma do CSS do shell (64rem).
export const CONSULTA_TELA_LARGA = '(min-width: 64rem)'

export function telaLarga() {
  return window.matchMedia(CONSULTA_TELA_LARGA).matches
}

// Ref que acompanha a largura da tela enquanto o componente existir.
export function useTelaLarga() {
  const consulta = window.matchMedia(CONSULTA_TELA_LARGA)
  const larga = ref(consulta.matches)
  const aoMudar = evento => {
    larga.value = evento.matches
  }
  consulta.addEventListener?.('change', aoMudar)
  onBeforeUnmount(() => consulta.removeEventListener?.('change', aoMudar))
  return larga
}
