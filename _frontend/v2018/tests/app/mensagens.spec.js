import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Vue from 'vue'
import Vuex from 'vuex'

import StoreMessage from '@/stores/message/StoreMessage'
import Message from '@/components/utils/message/Message'

Vue.use(Vuex)

describe('componente de mensagens', () => {
  it('V2018-EST-042: exibe a mensagem como texto', async () => {
    const store = new Vuex.Store({ modules: { store__message: StoreMessage } })
    const wrapper = mount(Message, { store })

    await store.dispatch('sendMessage', { alert: 'info', message: 'Salvo <b>com</b> sucesso', time: 5 })
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Salvo <b>com</b> sucesso')
    expect(wrapper.find('b').exists()).toBe(false)
  })
})
