import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { HttpError } from '~@/http/client'
import ModalWizard from '~@/overlays/ModalWizard.vue'
import {
  dadosIniciais,
  passosNovoCliente,
  validarIdentificacao,
  validarLocal
} from '~@/modules/demo/wizard/passos'
import { assentar, comOverlay, limparStores, overlayDeMentira } from './apoio'

const preenchido = {
  nome: 'Novo Modelo',
  email: 'novo.modelo@exemplo.invalid',
  cidade: 'Jataí',
  situacao: 'ativo',
  motivo: ''
}

function montar(concluir) {
  const overlay = overlayDeMentira()
  const wrapper = mount(ModalWizard, {
    props: { passos: passosNovoCliente, dadosIniciais: dadosIniciais(), concluir },
    global: { provide: comOverlay(overlay) },
    attachTo: document.body
  })
  return { wrapper, overlay }
}

function campo(wrapper, rotulo) {
  const label = wrapper.findAll('label').find(l => l.text() === rotulo)
  return wrapper.find(`[id="${label.attributes('for')}"]`)
}

function passoAtual(wrapper) {
  return wrapper.find('[aria-current="step"]').text()
}

async function avancar(wrapper) {
  await wrapper.find('[data-wizard-avancar]').trigger('click')
  await assentar()
}

describe('validação dos passos do wizard', () => {
  it('V8-DEMO-023: o primeiro passo exige nome com ao menos três letras', () => {
    expect(validarIdentificacao({ nome: '', email: 'a@exemplo.invalid' })).toEqual({
      nome: ['O nome precisa ter ao menos três letras.']
    })
    expect(Object.keys(validarIdentificacao({ nome: 'Jô', email: 'a@exemplo.invalid' }))).toEqual(['nome'])
    // Números e espaços não contam como letras.
    expect(Object.keys(validarIdentificacao({ nome: 'A1 2 3', email: 'a@exemplo.invalid' }))).toEqual(['nome'])
    expect(validarIdentificacao({ nome: 'Ana', email: 'a@exemplo.invalid' })).toEqual({})
    expect(validarIdentificacao({ nome: 'Zé É', email: 'a@exemplo.invalid' })).toEqual({})
  })

  it('V8-DEMO-023: o primeiro passo exige e-mail com @', () => {
    expect(validarIdentificacao({ nome: 'Ana', email: '' })).toEqual({
      email: ['Informe um e-mail válido.']
    })
    expect(Object.keys(validarIdentificacao({ nome: 'Ana', email: 'ana.exemplo.invalid' }))).toEqual(['email'])
    expect(Object.keys(validarIdentificacao({ nome: '', email: '' }))).toEqual(['nome', 'email'])
  })

  it('V8-DEMO-023: o segundo passo exige a cidade', () => {
    expect(validarLocal({ cidade: '   ', situacao: 'ativo', motivo: '' })).toEqual({
      cidade: ['Informe a cidade.']
    })
    expect(validarLocal({ cidade: 'Jataí', situacao: 'ativo', motivo: '' })).toEqual({})
  })

  it('V8-DEMO-023: o segundo passo exige o motivo só do cliente inativo', () => {
    expect(validarLocal({ cidade: 'Jataí', situacao: 'inativo', motivo: ' ' })).toEqual({
      motivo: ['Cliente inativo precisa de um motivo preenchido.']
    })
    expect(validarLocal({ cidade: 'Jataí', situacao: 'inativo', motivo: 'Cadastro duplicado' })).toEqual({})
  })

  it('V8-DEMO-023: o wizard tem três passos, e o último não barra a conclusão', () => {
    expect(passosNovoCliente.map(passo => passo.titulo)).toEqual(['Identificação', 'Local e situação', 'Revisão'])
    expect(passosNovoCliente.every(passo => typeof passo.componente === 'function')).toBe(true)
    expect(passosNovoCliente[0].validar).toBe(validarIdentificacao)
    expect(passosNovoCliente[1].validar).toBe(validarLocal)
    expect(passosNovoCliente[2].validar(dadosIniciais())).toEqual({})
    expect(dadosIniciais()).toEqual({ nome: '', email: '', cidade: '', situacao: 'ativo', motivo: '' })
  })
})

describe('wizard "Novo cliente" no ModalWizard', () => {
  afterEach(limparStores)

  it('V8-DEMO-023: percorre os três passos e envia os dados reunidos ao concluir', async () => {
    const criado = { id: 43, ...preenchido, desde: '2026-11-21', pedidos: [] }
    const concluir = vi.fn().mockResolvedValue(criado)
    const { wrapper, overlay } = montar(concluir)
    await assentar()

    expect(passoAtual(wrapper)).toBe('1. Identificação')
    await campo(wrapper, 'Nome').setValue(preenchido.nome)
    await campo(wrapper, 'E-mail').setValue(preenchido.email)
    expect(overlay.setDirty).toHaveBeenCalledWith(true)
    await avancar(wrapper)

    expect(passoAtual(wrapper)).toBe('2. Local e situação')
    await campo(wrapper, 'Cidade').setValue(preenchido.cidade)
    await avancar(wrapper)

    expect(passoAtual(wrapper)).toBe('3. Revisão')
    const revisao = wrapper.find('dl.v8-lista-dados').text()
    expect(revisao).toContain('Novo Modelo')
    expect(revisao).toContain('novo.modelo@exemplo.invalid')
    expect(revisao).toContain('Jataí')
    expect(revisao).toContain('Ativo')
    expect(wrapper.find('input').exists()).toBe(false)
    expect(concluir).not.toHaveBeenCalled()
    expect(wrapper.find('[data-wizard-avancar]').text()).toBe('Concluir')
    await avancar(wrapper)

    expect(concluir).toHaveBeenCalledWith(preenchido)
    expect(overlay.close).toHaveBeenCalledWith(criado)
    wrapper.unmount()
  })

  it('V8-DEMO-023: não avança com o passo inválido e mostra o erro junto ao campo', async () => {
    const { wrapper } = montar(vi.fn())
    await assentar()
    await campo(wrapper, 'Nome').setValue('Jô')
    await avancar(wrapper)

    expect(passoAtual(wrapper)).toBe('1. Identificação')
    expect(campo(wrapper, 'Nome').attributes('aria-invalid')).toBe('true')
    expect(campo(wrapper, 'E-mail').attributes('aria-invalid')).toBe('true')
    expect(wrapper.findAll('.v8-erro-campo').map(p => p.text())).toEqual([
      'O nome precisa ter ao menos três letras.',
      'Informe um e-mail válido.'
    ])
    wrapper.unmount()
  })

  it('V8-DEMO-023: cliente inativo só passa do segundo passo com o motivo', async () => {
    const { wrapper } = montar(vi.fn())
    await assentar()
    await campo(wrapper, 'Nome').setValue(preenchido.nome)
    await campo(wrapper, 'E-mail').setValue(preenchido.email)
    await avancar(wrapper)
    await campo(wrapper, 'Cidade').setValue(preenchido.cidade)
    await campo(wrapper, 'Situação').setValue('inativo')
    await avancar(wrapper)

    expect(passoAtual(wrapper)).toBe('2. Local e situação')
    expect(wrapper.find('.v8-erro-campo').text()).toBe('Cliente inativo precisa de um motivo preenchido.')

    await campo(wrapper, 'Motivo da inativação').setValue('Cadastro duplicado')
    await avancar(wrapper)
    expect(passoAtual(wrapper)).toBe('3. Revisão')
    expect(wrapper.find('dl.v8-lista-dados').text()).toContain('Cadastro duplicado')
    wrapper.unmount()
  })

  it('V8-DEMO-023: voltar mantém o que já foi preenchido', async () => {
    const { wrapper } = montar(vi.fn())
    await assentar()
    await campo(wrapper, 'Nome').setValue(preenchido.nome)
    await campo(wrapper, 'E-mail').setValue(preenchido.email)
    await avancar(wrapper)
    await wrapper.find('[data-wizard-voltar]').trigger('click')
    await assentar()

    expect(passoAtual(wrapper)).toBe('1. Identificação')
    expect(campo(wrapper, 'Nome').element.value).toBe(preenchido.nome)
    expect(campo(wrapper, 'E-mail').element.value).toBe(preenchido.email)
    wrapper.unmount()
  })

  it('V8-DEMO-023: erro de validação da API ao concluir aparece no wizard, que continua aberto', async () => {
    const concluir = vi.fn().mockRejectedValue(new HttpError({
      status: 400,
      codigo: 'validacao',
      campos: { email: ['Este e-mail já é usado por outro cliente.'] }
    }))
    const { wrapper, overlay } = montar(concluir)
    await assentar()
    await campo(wrapper, 'Nome').setValue(preenchido.nome)
    await campo(wrapper, 'E-mail').setValue(preenchido.email)
    await avancar(wrapper)
    await campo(wrapper, 'Cidade').setValue(preenchido.cidade)
    await avancar(wrapper)
    await avancar(wrapper)

    expect(concluir).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.v8-alerta-erro[role="alert"]').text()).toContain('Este e-mail já é usado por outro cliente.')
    expect(overlay.close).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})
