import { shallowMount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import PclFiltros from '@/modules/loa/pcl/PclFiltros.vue'

const montar = () => shallowMount(PclFiltros, {
  propsData: {
    value: {
      dash_activated: true,
      unidade: null,
      entidade: null,
      parlamentares: null,
      situacao: [],
      emendas_tipos: [],
      ajustes: 'False',
      search: ''
    },
    loasChoice: [{ value: 2026, text: 2026 }, { value: 2025, text: 2025 }],
    selectedLoaIds: [2026],
    lockedLoaId: 2026
  }
})

describe('filtros da prestação de contas', () => {
  // o componente avisa a página de que os filtros estão carregando
  beforeEach(() => {
    window.loadingCMJ = vi.fn()
    window.unloadingCMJ = vi.fn()
  })
  afterEach(() => {
    delete window.loadingCMJ
    delete window.unloadingCMJ
  })

  it('LOA-PCL-093: o ícone de cada exercício leva à prestação de contas dele', () => {
    const links = montar().findAll('a.btn-change-principal').wrappers

    expect(links.map(a => a.attributes('href'))).toEqual([
      '/loa/2026/prestacaoconta',
      '/loa/2025/prestacaoconta'
    ])
    expect(links[0].attributes('title')).toBe('Tornar este exercício o principal')
  })
})
