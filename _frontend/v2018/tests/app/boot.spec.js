// Subida da entrada `app` (src/main.js) em jsdom. A camada jQuery de `src/__globals` fica de fora:
// os plugins dela dependem do carregador AMD do webpack (veja docs/specs/v2018/testes.md).
import { describe, expect, it, vi } from 'vitest'
import Vue from 'vue'
import axios from 'axios'

import { esperar } from '../apoio'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso({ data: { is_authenticated: false } }))
vi.mock('@/__globals', () => ({}))

describe('entrada app', () => {
  it('V2018-EST-030, V2018-EST-031, V2018-EST-035: monta <App/> em #app, compila o HTML com [[ ]] e consulta /api/version', async () => {
    document.body.innerHTML = '<div id="app"><App/><span id="conta">[[ 1 + 1 ]]</span></div>'

    await import('@/main')
    await esperar()

    // V2018-EST-031
    expect(window.$).toBeTypeOf('function')
    expect(window.jQuery).toBe(window.$)

    // V2018-EST-030: o Vue assume #app, e o HTML que já estava lá vira template.
    expect(document.getElementById('app-vue')).not.toBeNull()
    expect(document.getElementById('conta').textContent).toBe('2')

    // V2018-EST-035
    ;['App', 'AppPntp', 'AppMenuPntp', 'AppListPntp', 'AppDoclistPntp'].forEach(nome => {
      expect(Vue.component(nome), nome).toBeDefined()
    })

    // Ao montar, App consulta a sessão.
    const urls = axios.mock.calls.map(chamada => chamada[0].url)
    expect(urls).toContain('/api/version')
  })
})
