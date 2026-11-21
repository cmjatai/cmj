import { beforeEach, describe, expect, it, vi } from 'vitest'
import Vue from 'vue'
import Vuex from 'vuex'

import VuexStore from '@/store'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

Vue.use(Vuex)

describe('store Vuex', () => {
  let store

  beforeEach(() => {
    store = new Vuex.Store(VuexStore)
  })

  it('V2018-EST-033: tem os módulos store__auth, store__message, store__online e store__sync', () => {
    expect(Object.keys(store.state).sort()).toEqual(
      ['store__auth', 'store__message', 'store__online', 'store__sync'])
  })

  it('V2018-EST-033: só store__sync tem namespace', () => {
    const acoes = Object.keys(store._actions)
    expect(acoes).toContain('store__sync/fetchSync')
    expect(acoes).toContain('sendMessage')
    expect(acoes).toContain('loginStatus')
    expect(acoes).toContain('refreshState')
    expect(acoes.filter(nome => nome.includes('/')).every(nome => nome.startsWith('store__sync/'))).toBe(true)
    expect(Object.keys(store.getters).some(nome => nome.includes('/'))).toBe(false)
  })

  it('V2018-EST-041: store__sync guarda só o cache de dados buscados por HTTP', async () => {
    expect(Object.keys(store.state.store__sync)).toEqual(['data_cache'])
    const acoes = Object.keys(store._actions).filter(nome => nome.startsWith('store__sync/'))
    expect(acoes.some(nome => /socket|timer|cronometro/i.test(nome))).toBe(false)
  })

  it('V2018-EST-033: sendMessage e popMessage são ações globais e usam o _ fornecido pelo build', async () => {
    await store.dispatch('sendMessage', { alert: 'info', message: 'um', time: 5 })
    await store.dispatch('sendMessage', { alert: 'info', message: 'dois', time: 5 })
    expect(store.getters.getMessages.map(m => m.message)).toEqual(['dois', 'um'])

    await store.dispatch('popMessage', store.getters.getMessages[0].id)
    expect(store.getters.getMessages.map(m => m.message)).toEqual(['um'])
  })
})
