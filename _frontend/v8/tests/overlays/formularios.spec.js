import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, reactive } from 'vue'
import { HttpError } from '~@/http/client'
import CampoForm from '~@/overlays/CampoForm.vue'
import ErrosGerais from '~@/overlays/ErrosGerais.vue'
import { useFormModal } from '~@/overlays/useFormModal'
import { useModal } from '~@/overlays/useModal'
// Importado aqui para que a importação sob demanda do wizard já esteja resolvida nos testes.
import '~@/overlays/ModalWizard.vue'
import { assentar, dialogos, montarHost, novoStore } from './apoio'

let store
let host

function erroDeValidacao(campos, gerais = []) {
  return new HttpError({ status: 400, codigo: 'validacao', mensagem: 'Corrija os campos.', campos, gerais })
}

function formulario(enviar) {
  return defineComponent({
    setup() {
      const valores = reactive({ nome: '', email: '' })
      const f = useFormModal({ valores, enviar })
      const campo = nome => h(CampoForm, { rotulo: nome, erro: f.erroDe(nome) }, {
        default: c => h('input', {
          id: c.id,
          name: nome,
          value: valores[nome],
          'aria-invalid': c.invalido,
          'aria-describedby': c.descritoPor,
          onInput: e => (valores[nome] = e.target.value)
        })
      })
      return () => h('form', { onSubmit: e => { e.preventDefault(); f.submeter(e) } }, [
        h(ErrosGerais, { mensagens: f.gerais.value }),
        campo('nome'),
        campo('email'),
        h('button', { type: 'submit', disabled: f.enviando.value, 'data-salvar': '' }, 'Salvar')
      ])
    }
  })
}

function digitar(nome, valor) {
  const campo = document.querySelector(`input[name="${nome}"]`)
  campo.value = valor
  campo.dispatchEvent(new Event('input'))
}

function enviarForm() {
  document.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
}

beforeEach(() => {
  store = novoStore()
  host = montarHost()
})

afterEach(() => {
  host.unmount()
  store.$limpar()
})

describe('modal de formulário', () => {
  it('V8-OVL-064: erro de validação mantém o modal aberto e aparece junto ao campo e no topo', async () => {
    const enviar = vi.fn().mockRejectedValue(erroDeValidacao(
      { email: ['E-mail já usado por outro cliente.'] },
      ['Situação inativa exige motivo.']
    ))
    let resolvido = 'aberto'
    useModal().openForm(formulario(enviar), {}, { title: 'Editar' }).then(v => (resolvido = v))
    await assentar()
    digitar('nome', 'Ana')
    enviarForm()
    await assentar()

    expect(enviar).toHaveBeenCalledWith({ nome: 'Ana', email: '' })
    expect(store.pilha).toHaveLength(1)
    expect(resolvido).toBe('aberto')
    const email = document.querySelector('input[name="email"]')
    expect(email.getAttribute('aria-invalid')).toBe('true')
    expect(document.getElementById(email.getAttribute('aria-describedby')).textContent.trim())
      .toBe('E-mail já usado por outro cliente.')
    expect(document.querySelector('input[name="nome"]').hasAttribute('aria-invalid')).toBe(false)
    expect(dialogos()[0].querySelector('[role="alert"]').textContent).toContain('Situação inativa exige motivo.')
    // O foco vai para o primeiro campo com erro.
    expect(document.activeElement).toBe(email)
  })

  it('V8-OVL-064: em sucesso o modal fecha e resolve com a resposta', async () => {
    const enviar = vi.fn().mockResolvedValue({ id: 7, nome: 'Ana' })
    const resultado = useModal().openForm(formulario(enviar), {}, { title: 'Editar' })
    await assentar()
    digitar('nome', 'Ana')
    enviarForm()
    expect(await resultado).toEqual({ id: 7, nome: 'Ana' })
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-064: erro que não é de validação aparece no topo', async () => {
    const enviar = vi.fn().mockRejectedValue(new HttpError({ status: 500, codigo: 'servidor', mensagem: 'Erro no servidor.' }))
    useModal().openForm(formulario(enviar), {}, { title: 'Editar' })
    await assentar()
    enviarForm()
    await assentar()
    expect(store.pilha).toHaveLength(1)
    expect(dialogos()[0].querySelector('[role="alert"]').textContent).toContain('Erro no servidor.')
  })

  it('V8-HTTP-044: mensagem de erro do servidor entra como texto, nunca como HTML', async () => {
    const hostil = '<img src=x onerror=alert(1)>'
    const enviar = vi.fn().mockRejectedValue(erroDeValidacao({ email: [hostil] }, [hostil]))
    useModal().openForm(formulario(enviar), {}, { title: 'Editar' })
    await assentar()
    enviarForm()
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.querySelector('img')).toBeNull()
    expect(dialogo.querySelector('.v8-erro-campo').textContent.trim()).toBe(hostil)
    expect(dialogo.querySelector('[role="alert"] li').textContent.trim()).toBe(hostil)
  })

  it('V8-OVL-065: marca alterado ao editar, desmarca ao salvar e trava o botão durante o envio', async () => {
    let liberar
    const enviar = vi.fn(() => new Promise(ok => (liberar = ok)))
    useModal().openForm(formulario(enviar), {}, { title: 'Editar' })
    await assentar()
    expect(store.topo.dirty).toBe(false)
    digitar('nome', 'Ana')
    await assentar()
    expect(store.topo.dirty).toBe(true)

    enviarForm()
    await assentar()
    expect(document.querySelector('[data-salvar]').disabled).toBe(true)
    enviarForm()
    expect(enviar).toHaveBeenCalledTimes(1)
    liberar({ ok: true })
    await assentar()
    expect(store.pilha).toHaveLength(0)
  })
})

describe('modal em passos', () => {
  const passo = campo => defineComponent({
    props: { dados: { type: Object, required: true }, erros: { type: Object, default: () => ({}) } },
    setup(props) {
      return () => h('div', { 'data-passo': campo }, [
        h('input', {
          name: campo,
          value: props.dados[campo],
          // eslint-disable-next-line vue/no-mutating-props
          onInput: e => (props.dados[campo] = e.target.value)
        }),
        props.erros[campo] ? h('p', { 'data-erro': campo }, props.erros[campo][0]) : null
      ])
    }
  })

  function passos() {
    return [
      { titulo: 'Identificação', componente: passo('nome'), validar: d => (d.nome ? {} : { nome: 'Informe o nome.' }) },
      { titulo: 'Local', componente: () => Promise.resolve({ default: passo('cidade') }) }
    ]
  }

  it('V8-OVL-066: só avança com o passo válido, volta sem perder e resolve com os dados', async () => {
    const resultado = useModal().openWizard({ title: 'Novo cliente', passos: passos(), dados: { nome: '', cidade: '' } })
    await assentar()
    const avancar = () => document.querySelector('[data-wizard-avancar]').click()

    avancar()
    await assentar()
    expect(document.querySelector('[data-passo="nome"]')).not.toBeNull()
    expect(document.querySelector('[data-erro="nome"]').textContent).toBe('Informe o nome.')

    digitar('nome', 'Ana')
    avancar()
    await assentar()
    expect(document.querySelector('[data-passo="cidade"]')).not.toBeNull()
    expect(document.querySelector('[data-wizard-avancar]').textContent.trim()).toBe('Concluir')
    digitar('cidade', 'Jataí')

    document.querySelector('[data-wizard-voltar]').click()
    await assentar()
    expect(document.querySelector('input[name="nome"]').value).toBe('Ana')
    avancar()
    await assentar()
    expect(document.querySelector('input[name="cidade"]').value).toBe('Jataí')

    avancar()
    expect(await resultado).toEqual({ nome: 'Ana', cidade: 'Jataí' })
  })

  it('V8-OVL-066: concluir envia os dados e os erros do servidor mantêm o modal aberto', async () => {
    const concluir = vi.fn()
      .mockRejectedValueOnce(erroDeValidacao({ email: ['E-mail inválido.'] }, ['Revise os dados.']))
      .mockResolvedValueOnce({ id: 99 })
    const resultado = useModal().openWizard({
      title: 'Novo',
      passos: [{ titulo: 'Único', componente: passo('nome') }],
      dados: { nome: 'Ana' },
      concluir
    })
    await assentar()
    document.querySelector('[data-wizard-avancar]').click()
    await assentar()
    expect(store.pilha).toHaveLength(1)
    const alerta = dialogos()[0].querySelector('[role="alert"]').textContent
    expect(alerta).toContain('Revise os dados.')
    expect(alerta).toContain('E-mail inválido.')

    document.querySelector('[data-wizard-avancar]').click()
    expect(await resultado).toEqual({ id: 99 })
    expect(concluir).toHaveBeenLastCalledWith({ nome: 'Ana' })
  })

  it('V8-OVL-024: o wizard preenchido pede confirmação antes de fechar', async () => {
    useModal().openWizard({ title: 'Novo', passos: passos(), dados: { nome: '', cidade: '' } })
    await assentar()
    digitar('nome', 'Ana')
    await assentar()
    expect(store.topo.dirty).toBe(true)
    dialogos()[0].querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(store.topo.type).toBe('confirm')
  })
})
