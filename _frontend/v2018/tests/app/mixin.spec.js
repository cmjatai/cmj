import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Vue from 'vue'
import Vuex from 'vuex'

import VuexStore from '@/store'
import Resources from '@/resources'
import { EventBus } from '@/event-bus'
import '@/mixins'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

Vue.use(Vuex)

const Componente = { template: '<p>teste</p>' }
const montar = (opcoes = {}) => mount({ ...Componente, ...opcoes }, { store: new Vuex.Store(VuexStore) })

describe('mixin global', () => {
  it('V2018-EST-034: todo componente recebe utils, o estado sincronizado e as ações comuns', () => {
    const vm = montar().vm

    expect(vm.utils).toBe(Resources.Utils)
    expect(vm.data_cache).toEqual({})
    expect(vm.user).toBeNull()
    expect(vm.permissions).toEqual([])
    expect(vm.nivel_detalhe).toBe(1)
    ;['fetchSync', 'sendMessage', 'refreshState', 'getObject', 'loginStatus'].forEach(nome => {
      expect(vm[nome]).toBeTypeOf('function')
    })
  })

  it('V2018-EST-034: user-logged-in e user-logged-out no EventBus chamam os métodos do componente', () => {
    const user_logged_in = vi.fn()
    const user_logged_out = vi.fn()
    montar({ methods: { user_logged_in, user_logged_out } })

    EventBus.$emit('user-logged-in')
    EventBus.$emit('user-logged-out')

    expect(user_logged_in).toHaveBeenCalledTimes(1)
    expect(user_logged_out).toHaveBeenCalledTimes(1)
  })

  it('V2018-EST-034: os listeners do EventBus saem quando o componente é destruído', () => {
    const user_logged_in = vi.fn()
    const wrapper = montar({ methods: { user_logged_in } })
    const vm = wrapper.vm
    const registrado = (evento, metodo) => EventBus._events[evento].includes(vm[metodo])
    expect(registrado('user-logged-in', 'user_logged_in')).toBe(true)
    expect(registrado('user-logged-out', 'user_logged_out')).toBe(true)

    wrapper.destroy()

    expect(registrado('user-logged-in', 'user_logged_in')).toBe(false)
    expect(registrado('user-logged-out', 'user_logged_out')).toBe(false)
    EventBus.$emit('user-logged-in')
    expect(user_logged_in).not.toHaveBeenCalled()
  })

  it('V2018-EST-041: o v2018 não tem cliente WebSocket', () => {
    expect(EventBus._events['ws-message']).toBeUndefined()
    expect(montar().vm.wsConnected).toBeUndefined()
  })
})
