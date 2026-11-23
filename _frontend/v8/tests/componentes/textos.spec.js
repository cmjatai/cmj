// Textos de interface dos componentes base em português (docs/specs/v8/componentes.md, V8-CMP-008).
import path from 'path'
import { afterEach, describe, expect, it } from 'vitest'
import DsCampos from '~@/modules/ds/ilhas/DsCampos.vue'
import DsComponentes from '~@/modules/ds/ilhas/DsComponentes.vue'
import DsCor from '~@/modules/ds/ilhas/DsCor.vue'
import DsDatas from '~@/modules/ds/ilhas/DsDatas.vue'
import DsEstrutura from '~@/modules/ds/ilhas/DsEstrutura.vue'
import Etapas from '~@/componentes/Etapas.vue'
import { assentar } from '../demo/apoio'
import { OFICIAL, desmontarTodos, ler, montar } from './apoio'

// O aviso de passo do Reka, em inglês, que o CSS do oficial esconde.
const AVISO_DO_REKA = '.v8-etapas > [role="status"]:not([data-etapas-aviso])'

// Palavras dos textos padrão do Reka UI em inglês.
const INGLES = /\b(increase|decrease|remove|show popup|next page|previous page|first page|last page|page \d|step \d|submit|cancel|edit|no options|color swatch|color picker|color thumb|pin input|day|month|year|hour|minute|second|progress)\b/i

// O jsdom não carrega o CSS: o que o oficial esconde é tirado pelo mesmo seletor.
function visivel(el) {
  return !el.closest(`[hidden], [aria-hidden="true"], ${AVISO_DO_REKA}`)
}

describe('textos dos componentes base', () => {
  afterEach(desmontarTodos)

  it('V8-CMP-008: os rótulos e textos que o Reka UI traz em inglês saem em português', async () => {
    ;[DsComponentes, DsCampos, DsEstrutura, DsDatas, DsCor].forEach(ilha => montar(ilha))
    await assentar()
    const achados = []
    document.querySelectorAll('*').forEach(el => {
      ;['aria-label', 'aria-roledescription', 'aria-valuetext', 'title', 'placeholder'].forEach(atributo => {
        const valor = el.getAttribute(atributo)
        if (valor && INGLES.test(valor)) {
          achados.push(`${atributo}="${valor}"`)
        }
      })
      // Texto próprio do elemento, sem o dos filhos, nas regiões que o leitor de tela anuncia.
      const proprio = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').trim()
      if (proprio && INGLES.test(proprio) && visivel(el)) {
        achados.push(`texto "${proprio}"`)
      }
    })
    expect(achados).toEqual([])
  })

  it('V8-CMP-008: o aviso de passo das etapas sai em português e o do Reka fica escondido', async () => {
    const etapas = montar(Etapas, { props: { modelValue: 2, passos: [{ titulo: 'A' }, { titulo: 'B' }, { titulo: 'C' }] } })
    await assentar()
    expect(etapas.find('[data-etapas-aviso]').text()).toBe('Etapa 2 de 3')
    const doReka = etapas.findAll('[role="status"]').filter(s => s.attributes('data-etapas-aviso') === undefined)
    expect(doReka).toHaveLength(1)
    expect(doReka[0].text()).toMatch(/Step 2 of 3/)
    expect(doReka[0].element.matches(AVISO_DO_REKA)).toBe(true)
    const css = ler(path.join(OFICIAL, 'estrutura.css')).replace(/\s+/g, ' ')
    expect(css).toContain(`${AVISO_DO_REKA} { display: none; }`)
  })
})
