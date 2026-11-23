// Componentes de cor (docs/specs/v8/componentes.md).
import fs from 'fs'
import path from 'path'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import AmostraCor from '~@/componentes/AmostraCor.vue'
import AreaCor from '~@/componentes/AreaCor.vue'
import CampoCor from '~@/componentes/CampoCor.vue'
import DeslizanteCor from '~@/componentes/DeslizanteCor.vue'
import PaletaCores from '~@/componentes/PaletaCores.vue'
import { ilhas } from '~@/core/ilhas'
import DsCor from '~@/modules/ds/ilhas/DsCor.vue'
import { assentar } from '../demo/apoio'
import { RAIZ, desmontarTodos, montar } from './apoio'

const CORES = [
  { valor: '#114d81', rotulo: 'Azul' },
  { valor: '#17754a', rotulo: 'Verde' }
]

describe('componentes de cor', () => {
  afterEach(() => {
    desmontarTodos()
    document.head.querySelectorAll('style[data-teste-cor]').forEach(el => el.remove())
  })

  it('V8-CMP-035: o v-model é a cor em hexadecimal', async () => {
    const paleta = montar(PaletaCores, { props: { opcoes: CORES, modelValue: '#17754a', rotulo: 'Cor' } })
    expect(paleta.find('[role="listbox"]').attributes('aria-label')).toBe('Cor')
    expect(paleta.findAll('[role="option"]').map(o => o.attributes('aria-selected'))).toEqual(['false', 'true'])
    expect(paleta.findAll('[role="option"]').map(o => o.attributes('aria-label'))).toEqual(['Azul', 'Verde'])
    await paleta.findAll('[role="option"]')[0].trigger('click')
    expect(paleta.emitted('update:modelValue').at(-1)).toEqual(['#114d81'])

    const amostra = montar(AmostraCor, { props: { cor: '#114d81', rotulo: 'Primária' } })
    expect(amostra.find('[role="img"]').attributes('aria-label')).toBe('Primária')

    const campo = montar(CampoCor, { props: { modelValue: '#114d81', rotulo: 'Cor' } })
    expect(campo.find('input.v8-campo-cor-entrada').element.value.toLowerCase()).toBe('#114d81')

    const deslizante = montar(DeslizanteCor, { props: { modelValue: '#114d81', canal: 'hue' } })
    await assentar()
    expect(deslizante.find('[role="slider"]').attributes('aria-label')).toBe('Matiz')

    const area = montar(AreaCor, { props: { modelValue: '#114d81' } })
    await assentar()
    expect(area.find('[role="slider"]').exists()).toBe(true)
  })

  it('V8-CMP-035: com name, a cor vai no formulário em hexadecimal', async () => {
    montar(defineComponent({
      setup: () => () =>
        h('form', { id: 'form-cor' }, [
          h(PaletaCores, { name: 'paleta', modelValue: '#17754a', opcoes: CORES }),
          h(AreaCor, { name: 'area', modelValue: '#114d81' }),
          h(DeslizanteCor, { name: 'matiz', modelValue: '#114d81' }),
          h(CampoCor, { name: 'campo', modelValue: '#114d81' })
        ])
    }))
    await assentar()
    const dados = new FormData(document.getElementById('form-cor'))
    expect(dados.get('paleta')).toBe('#17754a')
    expect(dados.get('area')).toBe('#114d81')
    expect(dados.get('matiz')?.toLowerCase()).toBe('#114d81')
    expect(dados.get('campo')?.toLowerCase()).toBe('#114d81')
  })

  it('V8-CMP-035: o código não tem cor literal, e a vitrine lê as cores dos tokens', async () => {
    const pastas = [path.join(RAIZ, 'src/componentes'), path.join(RAIZ, 'src/modules/ds')]
    const arquivos = pastas.flatMap(function ler(pasta) {
      return fs.readdirSync(pasta, { withFileTypes: true }).flatMap(item =>
        item.isDirectory() ? ler(path.join(pasta, item.name)) : [path.join(pasta, item.name)]
      )
    })
    arquivos.forEach(arquivo => {
      expect(fs.readFileSync(arquivo, 'utf8'), arquivo).not.toMatch(/#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|\b(rgba?|hsla?|oklch)\(/)
    })

    const estilo = document.createElement('style')
    estilo.dataset.testeCor = ''
    estilo.textContent = ':root { --cor-primaria: #114d81; --cor-perigo: #b3261e; --cor-sucesso: #17754a; }'
    document.head.appendChild(estilo)
    const ilha = montar(DsCor)
    await assentar()
    const opcoes = ilha.findAll('.v8-paleta-cores [role="option"]').map(o => o.attributes('aria-label'))
    expect(opcoes).toEqual(['--cor-primaria', '--cor-sucesso', '--cor-perigo'])
    expect(ilha.find('[data-ds-cor]').text()).toBe('#114d81')
  })

  it('V8-DS-018: a ilha ds-cor mostra os componentes de cor', async () => {
    expect(Object.hasOwn(ilhas, 'ds-cor')).toBe(true)
    const ilha = montar(DsCor)
    await assentar()
    ;[AreaCor, CampoCor, DeslizanteCor, PaletaCores].forEach(componente => {
      expect(ilha.findComponent(componente).exists(), componente.__name).toBe(true)
    })
  })
})
