import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { HttpError } from '~@/http/client'
import * as api from '~@/modules/demo/api'
import ClienteForm from '~@/modules/demo/modais/ClienteForm.vue'
import { assentar, clienteDeExemplo, comOverlay, limparStores, overlayDeMentira } from './apoio'

vi.mock('~@/modules/demo/api')

function montar(overlay = overlayDeMentira()) {
  const wrapper = mount(ClienteForm, {
    props: { cliente: clienteDeExemplo() },
    global: { provide: comOverlay(overlay) },
    attachTo: document.body
  })
  return { wrapper, overlay }
}

function campo(wrapper, rotulo) {
  const label = wrapper.findAll('label').find(l => l.text() === rotulo)
  return wrapper.find(`[id="${label.attributes('for')}"]`)
}

function botao(wrapper, texto) {
  return wrapper.findAll('button').find(b => b.text() === texto)
}

describe('modal de edição do cliente', () => {
  afterEach(limparStores)

  it('V8-DEMO-022: abre com os dados do cliente, sem marcar o modal como alterado', async () => {
    const { wrapper, overlay } = montar()
    await assentar()
    expect(campo(wrapper, 'Nome').element.value).toBe('Glória Exemplo')
    expect(campo(wrapper, 'E-mail').element.value).toBe('gloria.exemplo@exemplo.invalid')
    expect(campo(wrapper, 'Cidade').element.value).toBe('Jataí')
    expect(campo(wrapper, 'Situação').element.value).toBe('ativo')
    expect(campo(wrapper, 'Situação').findAll('option').map(o => o.element.value)).toEqual(['ativo', 'inativo'])
    expect(campo(wrapper, 'Motivo da inativação').element.value).toBe('')
    expect(overlay.setDirty).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('V8-DEMO-022: editar um campo marca o modal como alterado', async () => {
    const { wrapper, overlay } = montar()
    await campo(wrapper, 'Cidade').setValue('Mineiros')
    expect(overlay.setDirty).toHaveBeenCalledWith(true)
    wrapper.unmount()
  })

  it('V8-DEMO-022: "Cancelar" pede o fechamento com guarda, e não o fechamento direto', async () => {
    const { wrapper, overlay } = montar()
    await botao(wrapper, 'Cancelar').trigger('click')
    expect(overlay.dismiss).toHaveBeenCalledTimes(1)
    expect(overlay.close).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('V8-DEMO-022: erro de validação aparece junto ao campo e no topo, e o modal continua aberto', async () => {
    api.salvar.mockRejectedValue(new HttpError({
      status: 400,
      codigo: 'validacao',
      campos: { email: ['Este e-mail já é usado por outro cliente.'] },
      gerais: ['Cliente inativo precisa de um motivo preenchido.']
    }))
    const { wrapper, overlay } = montar()
    await campo(wrapper, 'E-mail').setValue('ana.exemplo@exemplo.invalid')
    await campo(wrapper, 'Situação').setValue('inativo')
    await wrapper.find('form').trigger('submit')
    await assentar()

    expect(api.salvar).toHaveBeenCalledWith(7, {
      nome: 'Glória Exemplo',
      email: 'ana.exemplo@exemplo.invalid',
      cidade: 'Jataí',
      situacao: 'inativo',
      motivo: ''
    })
    const email = campo(wrapper, 'E-mail')
    expect(email.attributes('aria-invalid')).toBe('true')
    const erroDoCampo = wrapper.find(`[id="${email.attributes('aria-describedby')}"]`)
    expect(erroDoCampo.classes()).toContain('v8-erro-campo')
    expect(erroDoCampo.text()).toBe('Este e-mail já é usado por outro cliente.')
    expect(campo(wrapper, 'Nome').attributes('aria-invalid')).toBeUndefined()

    const topo = wrapper.find('form > .v8-alerta-erro[role="alert"]')
    expect(topo.text()).toBe('Cliente inativo precisa de um motivo preenchido.')
    expect(wrapper.find('form').element.firstElementChild).toBe(topo.element)

    // O foco vai para o primeiro campo com erro, e nada é fechado.
    expect(document.activeElement).toBe(email.element)
    expect(overlay.close).not.toHaveBeenCalled()
    expect(botao(wrapper, 'Salvar').element.disabled).toBe(false)
    wrapper.unmount()
  })

  it('V8-DEMO-022: ao salvar, fecha o modal com a resposta da API e limpa a marca de alterado', async () => {
    const salvo = clienteDeExemplo({ cidade: 'Mineiros' })
    api.salvar.mockResolvedValue(salvo)
    const { wrapper, overlay } = montar()
    await campo(wrapper, 'Cidade').setValue('Mineiros')
    await wrapper.find('form').trigger('submit')
    await assentar()

    expect(api.salvar).toHaveBeenCalledTimes(1)
    expect(api.salvar.mock.calls[0][1].cidade).toBe('Mineiros')
    expect(overlay.setDirty).toHaveBeenLastCalledWith(false)
    expect(overlay.close).toHaveBeenCalledWith(salvo)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('V8-DEMO-022: durante o envio os botões ficam desabilitados', async () => {
    let concluir
    api.salvar.mockReturnValue(new Promise(resolver => {
      concluir = resolver
    }))
    const { wrapper, overlay } = montar()
    await wrapper.find('form').trigger('submit')
    expect(botao(wrapper, 'Salvando…').element.disabled).toBe(true)
    expect(botao(wrapper, 'Cancelar').element.disabled).toBe(true)

    // Um segundo envio com o primeiro em curso não vai à API.
    await wrapper.find('form').trigger('submit')
    expect(api.salvar).toHaveBeenCalledTimes(1)

    concluir(clienteDeExemplo())
    await assentar()
    expect(overlay.close).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('V8-DEMO-022: "Salvar" fica no rodapé do overlay, fora do formulário, e ainda o envia', async () => {
    api.salvar.mockResolvedValue(clienteDeExemplo())
    const rodapeEl = document.createElement('div')
    document.body.appendChild(rodapeEl)
    const { wrapper, overlay } = montar(overlayDeMentira({ rodapeEl }))
    await assentar()

    const salvar = [...rodapeEl.querySelectorAll('button')].find(b => b.textContent.trim() === 'Salvar')
    const formulario = wrapper.find('form').element
    expect(formulario.contains(salvar)).toBe(false)
    expect(salvar.getAttribute('type')).toBe('submit')
    expect(salvar.getAttribute('form')).toBe(formulario.id)
    expect(salvar.form).toBe(formulario)

    salvar.click()
    await assentar()
    expect(api.salvar).toHaveBeenCalledTimes(1)
    expect(overlay.close).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('V8-DEMO-022: falha que não é de validação aparece no topo e mantém o modal aberto', async () => {
    api.salvar.mockRejectedValue(new HttpError({ status: 500, codigo: 'servidor' }))
    const { wrapper, overlay } = montar()
    await wrapper.find('form').trigger('submit')
    await assentar()
    expect(wrapper.find('[role="alert"]').text()).toContain('O servidor encontrou um erro.')
    expect(overlay.close).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})
