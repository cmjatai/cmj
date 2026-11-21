import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Vue from 'vue'

import Pagination from '@/components/Pagination'

describe('ambiente de testes', () => {
  it('V2018-TST-002: roda em jsdom com Vue 2', () => {
    expect(window.document).toBeDefined()
    expect(Vue.version.startsWith('2.')).toBe(true)
  })

  it('V2018-TST-004: compila template em tempo de execução', () => {
    const wrapper = mount({ template: '<p>{{ a + b }}</p>', data: () => ({ a: 1, b: 2 }) })
    expect(wrapper.text()).toBe('3')
  })

  it('V2018-TST-004: fornece $, jQuery e _ aos arquivos de src sem import', async () => {
    const { default: AppLOA } = await import('@/__apps/loa/AppLOA')
    // isObjectEmpty usa `_` sem importar lodash.
    expect(AppLOA.isObjectEmpty({ a: [], b: '' })).toBe(true)
    expect(AppLOA.isObjectEmpty({ a: [1] })).toBe(false)
  })

  it('V2018-TST-020: bloqueia requisições de rede reais', () => {
    expect(() => window.fetch('/api/version')).toThrow(/rede/)
    expect(() => new window.WebSocket('ws://localhost/ws/sync/')).toThrow(/rede/)
    const xhr = new window.XMLHttpRequest()
    xhr.open('GET', '/api/version')
    expect(() => xhr.send()).toThrow(/rede/)
  })

  it('V2018-TST-004: resolve o alias @ e monta um componente .vue sem extensão no import', () => {
    expect(Pagination).toBeTypeOf('object')
    expect(Pagination.render || Pagination.template).toBeDefined()
  })
})
