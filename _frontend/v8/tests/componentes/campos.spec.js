// Componentes de campo (docs/specs/v8/componentes.md, grupo "Campos").
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import Alternador from '~@/componentes/Alternador.vue'
import Autocompletar from '~@/componentes/Autocompletar.vue'
import Avaliacao from '~@/componentes/Avaliacao.vue'
import CampoCodigo from '~@/componentes/CampoCodigo.vue'
import CampoEtiquetas from '~@/componentes/CampoEtiquetas.vue'
import CampoNumero from '~@/componentes/CampoNumero.vue'
import Deslizante from '~@/componentes/Deslizante.vue'
import GrupoAlternadores from '~@/componentes/GrupoAlternadores.vue'
import GrupoEtiquetas from '~@/componentes/GrupoEtiquetas.vue'
import ListaOpcoes from '~@/componentes/ListaOpcoes.vue'
import Rotulo from '~@/componentes/Rotulo.vue'
import SelecaoBusca from '~@/componentes/SelecaoBusca.vue'
import TextoEditavel from '~@/componentes/TextoEditavel.vue'
import { ilhas } from '~@/core/ilhas'
import DsCampos from '~@/modules/ds/ilhas/DsCampos.vue'
import { assentar } from '../demo/apoio'
import { desmontarTodos, montar } from './apoio'

const OPCOES = [
  { valor: 'centro', rotulo: 'Centro' },
  { valor: 'norte', rotulo: 'Norte' },
  { valor: 'sul', rotulo: 'Sul' }
]

function noFormulario(filhos) {
  montar(defineComponent({ setup: () => () => h('form', { id: 'form-campos' }, filhos()) }))
}

const dadosDoFormulario = () => new FormData(document.getElementById('form-campos'))

describe('componentes de campo', () => {
  afterEach(desmontarTodos)

  it('V8-CMP-010: cada campo usa a sua primitiva e devolve o valor pelo v-model', async () => {
    const rotulo = montar(Rotulo, { props: { para: 'x', texto: 'Nome' } })
    expect(rotulo.find('label.v8-rotulo').attributes('for')).toBe('x')

    const alternador = montar(Alternador, { props: { modelValue: false, texto: 'N' } })
    await alternador.find('button').trigger('click')
    expect(alternador.emitted('update:modelValue')).toEqual([[true]])
    expect(alternador.find('button').attributes('data-state')).toBe('on')

    const grupo = montar(GrupoAlternadores, { props: { itens: OPCOES, modelValue: 'norte', rotulo: 'Região' } })
    expect(grupo.find('[role="group"]').attributes('aria-label')).toBe('Região')
    await grupo.findAll('button')[2].trigger('click')
    expect(grupo.emitted('update:modelValue')).toEqual([['sul']])

    const deslizante = montar(Deslizante, { props: { modelValue: 4, max: 10, rotulo: 'Volume' } })
    await assentar()
    const pino = deslizante.find('[role="slider"]')
    expect(pino.attributes('aria-valuenow')).toBe('4')
    expect(pino.attributes('aria-label')).toBe('Volume')
    const intervalo = montar(Deslizante, { props: { modelValue: [20, 70], rotulo: 'Faixa' } })
    expect(intervalo.findAll('[role="slider"]').map(p => p.attributes('aria-label'))).toEqual([
      'Faixa, mínimo',
      'Faixa, máximo'
    ])

    const codigo = montar(CampoCodigo, { props: { modelValue: '12', tamanho: 4 } })
    expect(codigo.findAll('input.v8-campo-codigo-casa').map(i => i.element.value)).toEqual(['1', '2', '', ''])

    const etiquetas = montar(CampoEtiquetas, { props: { modelValue: ['Saúde', 'Orçamento'] } })
    expect(etiquetas.findAll('.v8-campo-etiquetas-item').map(i => i.text())).toEqual(['Saúde', 'Orçamento'])

    const editavel = montar(TextoEditavel, { props: { modelValue: 'Sessão' } })
    expect(editavel.text()).toContain('Sessão')

    const avaliacao = montar(Avaliacao, { props: { modelValue: 3, rotulo: 'Nota' } })
    expect(avaliacao.find('[role="radiogroup"]').exists()).toBe(true)
    expect(avaliacao.findAll('.v8-avaliacao-estrela[data-state="active"]')).toHaveLength(3)

    const busca = montar(SelecaoBusca, { props: { opcoes: OPCOES, modelValue: 'norte', rotulo: 'Bairro' } })
    expect(busca.find('[role="combobox"]').element.value).toBe('Norte')

    const sugestoes = montar(Autocompletar, { props: { sugestoes: ['Jataí'], modelValue: 'Ja', rotulo: 'Cidade' } })
    expect(sugestoes.find('[role="combobox"]').element.value).toBe('Ja')

    const lista = montar(ListaOpcoes, { props: { opcoes: OPCOES, modelValue: 'sul', rotulo: 'Região' } })
    expect(lista.find('[role="listbox"]').attributes('aria-label')).toBe('Região')
    expect(lista.findAll('[role="option"]').map(o => o.attributes('aria-selected'))).toEqual(['false', 'false', 'true'])

    const grupoEtiquetas = montar(GrupoEtiquetas, { props: { itens: OPCOES, removivel: true } })
    expect(grupoEtiquetas.findAll('[role="row"]')).toHaveLength(3)
    await grupoEtiquetas.findAll('.v8-campo-etiquetas-remover')[1].trigger('click')
    expect(grupoEtiquetas.emitted('remover')?.[0]?.[0]).toEqual(['norte'])
    const fixas = montar(GrupoEtiquetas, { props: { itens: OPCOES } })
    expect(fixas.findAll('.v8-campo-etiquetas-remover')).toHaveLength(0)
  })

  it('V8-CMP-010: com name, dentro de um form, os campos entram no envio nativo', async () => {
    noFormulario(() => [
      h(GrupoAlternadores, { name: 'alinhamento', modelValue: 'centro', itens: OPCOES }),
      h(Deslizante, { name: 'volume', modelValue: 7 }),
      h(CampoNumero, { name: 'valor', modelValue: 1250.5 }),
      h(CampoCodigo, { name: 'codigo', modelValue: '1234', tamanho: 4 }),
      h(CampoEtiquetas, { name: 'assuntos', modelValue: ['Saúde', 'Orçamento'] }),
      h(TextoEditavel, { name: 'titulo', modelValue: 'Sessão' }),
      h(Avaliacao, { name: 'nota', modelValue: 4 }),
      h(SelecaoBusca, { name: 'bairro', modelValue: 'norte', opcoes: OPCOES }),
      h(Autocompletar, { name: 'cidade', modelValue: 'Jataí', sugestoes: ['Jataí'] }),
      h(ListaOpcoes, { name: 'regiao', modelValue: 'sul', opcoes: OPCOES }),
      h(Alternador, { name: 'negrito', modelValue: true, texto: 'N' }),
      h(Alternador, { name: 'italico', modelValue: false, texto: 'I' }),
      h(Alternador, { name: 'sublinhado', value: 'sim', modelValue: true, texto: 'S' })
    ])
    await assentar()
    const dados = dadosDoFormulario()
    expect(dados.get('alinhamento')).toBe('centro')
    expect(dados.get('volume[0]')).toBe('7')
    expect(dados.get('valor')).toBe('1250.5')
    expect(dados.get('codigo')).toBe('1234')
    expect([dados.get('assuntos[0]'), dados.get('assuntos[1]')]).toEqual(['Saúde', 'Orçamento'])
    expect(dados.get('titulo')).toBe('Sessão')
    expect(dados.get('nota')).toBe('4')
    expect(dados.get('bairro')).toBe('norte')
    expect(dados.get('cidade')).toBe('Jataí')
    expect(dados.get('regiao')).toBe('sul')
    // O Alternador vai como uma caixa de marcação: o value só quando pressionado (D6).
    expect(dados.get('negrito')).toBe('on')
    expect(dados.get('italico')).toBeNull()
    expect(dados.get('sublinhado')).toBe('sim')
  })

  it('V8-CMP-011: o campo de número formata em pt-BR e envia o número cru', async () => {
    noFormulario(() => [
      h(CampoNumero, { name: 'valor', modelValue: 1250.5, formato: { style: 'currency', currency: 'BRL' } }),
      h(CampoNumero, { name: 'quantidade', modelValue: 12345.678, formato: { maximumFractionDigits: 2 } })
    ])
    await assentar()
    const visiveis = [...document.querySelectorAll('input.v8-campo-numero-entrada')].map(i => i.value)
    expect(visiveis[0].replace(/\s/g, ' ')).toBe('R$ 1.250,50')
    expect(visiveis[1]).toBe('12.345,68')
    const dados = dadosDoFormulario()
    expect(dados.get('valor')).toBe('1250.5')
    expect(dados.get('quantidade')).toBe('12345.678')
  })

  it('V8-DS-015: a ilha ds-campos mostra os componentes de campo', async () => {
    expect(Object.hasOwn(ilhas, 'ds-campos')).toBe(true)
    const ilha = montar(DsCampos)
    await assentar()
    ;[Rotulo, Alternador, GrupoAlternadores, Deslizante, CampoNumero, CampoCodigo, CampoEtiquetas, TextoEditavel,
      Avaliacao, SelecaoBusca, Autocompletar, ListaOpcoes, GrupoEtiquetas].forEach(componente => {
      expect(ilha.findComponent(componente).exists(), componente.__name).toBe(true)
    })
  })
})
