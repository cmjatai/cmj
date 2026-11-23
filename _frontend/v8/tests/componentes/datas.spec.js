// Componentes de data e hora (docs/specs/v8/componentes.md).
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import Calendario from '~@/componentes/Calendario.vue'
import CalendarioPeriodo from '~@/componentes/CalendarioPeriodo.vue'
import CampoData from '~@/componentes/CampoData.vue'
import CampoHora from '~@/componentes/CampoHora.vue'
import CampoIntervaloHoras from '~@/componentes/CampoIntervaloHoras.vue'
import CampoPeriodo from '~@/componentes/CampoPeriodo.vue'
import SeletorAno from '~@/componentes/SeletorAno.vue'
import SeletorAnos from '~@/componentes/SeletorAnos.vue'
import SeletorData from '~@/componentes/SeletorData.vue'
import SeletorMes from '~@/componentes/SeletorMes.vue'
import SeletorMeses from '~@/componentes/SeletorMeses.vue'
import SeletorPeriodo from '~@/componentes/SeletorPeriodo.vue'
import { ano, dia, hora, mes, periodoParaObjeto, periodoParaTexto } from '~@/componentes/datas'
import { ilhas } from '~@/core/ilhas'
import DsDatas from '~@/modules/ds/ilhas/DsDatas.vue'
import { assentar } from '../demo/apoio'
import { desmontarTodos, montar } from './apoio'

const celula = (wrapper, valor) => wrapper.find(`[data-value="${valor}"]`)

describe('componentes de data e hora', () => {
  afterEach(desmontarTodos)

  it('V8-CMP-030: o v-model é texto ISO, e texto inválido vale como vazio', () => {
    expect(dia.paraTexto(dia.paraObjeto('2026-11-22'))).toBe('2026-11-22')
    expect(hora.paraTexto(hora.paraObjeto('07:05'))).toBe('07:05')
    expect(mes.paraTexto(mes.paraObjeto('2026-02'))).toBe('2026-02')
    expect(ano.paraTexto(ano.paraObjeto('2026'))).toBe('2026')
    ;['', null, undefined, '22/11/2026', '2026-13-01', '2026-02-30', 'abc'].forEach(texto => {
      expect(dia.paraObjeto(texto), String(texto)).toBeUndefined()
    })
    ;['', '24:00', '7:05', '14:30:00'].forEach(texto => expect(hora.paraObjeto(texto), texto).toBeUndefined())
    ;['', '2026-13', '2026-00', '2026'].forEach(texto => expect(mes.paraObjeto(texto), texto).toBeUndefined())
    ;['', '26', '2026-01'].forEach(texto => expect(ano.paraObjeto(texto), texto).toBeUndefined())
    expect(dia.paraTexto(undefined)).toBe('')
    expect(periodoParaTexto(periodoParaObjeto({ inicio: '2026-01-02', fim: 'x' }, dia), dia)).toEqual({
      inicio: '2026-01-02',
      fim: ''
    })
    expect(periodoParaTexto(periodoParaObjeto(null, mes), mes)).toEqual({ inicio: '', fim: '' })
  })

  it('V8-CMP-030: o calendário mostra o dia do v-model, em pt-BR, e devolve o escolhido em ISO', async () => {
    const calendario = montar(Calendario, { props: { modelValue: '2026-11-22', rotulo: 'Data' } })
    await assentar()
    expect(celula(calendario, '2026-11-22').attributes('data-selected')).toBeDefined()
    expect(calendario.find('.v8-calendario-titulo').text().toLowerCase()).toContain('novembro')
    expect(calendario.findAll('.v8-calendario-dia-semana')).toHaveLength(7)
    await celula(calendario, '2026-11-25').trigger('click')
    expect(calendario.emitted('update:modelValue').at(-1)).toEqual(['2026-11-25'])

    const periodo = montar(CalendarioPeriodo, { props: { modelValue: { inicio: '2026-11-10', fim: '2026-11-20' } } })
    await assentar()
    expect(celula(periodo, '2026-11-10').attributes('data-selection-start')).toBeDefined()
    expect(celula(periodo, '2026-11-20').attributes('data-selection-end')).toBeDefined()
  })

  it('V8-CMP-030: os campos por partes mostram DD/MM/AAAA, e hora em 24 horas', async () => {
    const data = montar(CampoData, { props: { modelValue: '2026-11-05', rotulo: 'Data' } })
    await assentar()
    const partes = data.findAll('.v8-campo-data-segmento').map(s => s.text())
    expect(partes).toEqual(['05', '11', '2026'])
    // O usuário vê e digita DD/MM/AAAA.
    expect(data.find('.v8-campo-data').text().replace(/\s/g, '')).toBe('05/11/2026')
    expect(data.find('[role="group"]').attributes('aria-label')).toBe('Data')

    const horario = montar(CampoHora, { props: { modelValue: '14:30' } })
    await assentar()
    expect(horario.findAll('.v8-campo-data-segmento').map(s => s.text())).toEqual(['14', '30'])

    const intervalo = montar(CampoIntervaloHoras, { props: { modelValue: { inicio: '08:00', fim: '18:00' } } })
    await assentar()
    expect(intervalo.findAll('.v8-campo-data-segmento').map(s => s.text())).toEqual(['08', '00', '18', '00'])

    const vigencia = montar(CampoPeriodo, { props: { modelValue: { inicio: '2026-01-01', fim: '2026-12-31' } } })
    await assentar()
    expect(vigencia.findAll('.v8-campo-data-segmento').map(s => s.text()).join(' ')).toBe('01 01 2026 31 12 2026')
  })

  it('V8-CMP-031: mês e ano saem sem o dia nem o mês de hoje', async () => {
    const competencia = montar(SeletorMes, { props: { modelValue: '2026-11' } })
    await assentar()
    expect(celula(competencia, '2026-11-01').attributes('data-selected')).toBeDefined()
    await celula(competencia, '2026-12-01').trigger('click')
    expect(competencia.emitted('update:modelValue').at(-1)).toEqual(['2026-12'])

    const exercicio = montar(SeletorAno, { props: { modelValue: '2026' } })
    await assentar()
    expect(celula(exercicio, '2026-01-01').attributes('data-selected')).toBeDefined()
    await celula(exercicio, '2027-01-01').trigger('click')
    expect(exercicio.emitted('update:modelValue').at(-1)).toEqual(['2027'])

    const meses = montar(SeletorMeses, { props: { modelValue: { inicio: '2026-01', fim: '2026-03' } } })
    await assentar()
    expect(celula(meses, '2026-01-01').attributes('data-selection-start')).toBeDefined()
    const anos = montar(SeletorAnos, { props: { modelValue: { inicio: '2025', fim: '2028' } } })
    await assentar()
    expect(celula(anos, '2028-01-01').attributes('data-selection-end')).toBeDefined()
  })

  it('V8-CMP-031: com name, o valor vai no formulário em ISO, e o período vazio vai vazio', async () => {
    montar(defineComponent({
      setup: () => () =>
        h('form', { id: 'form-datas' }, [
          h(Calendario, { name: 'dia', modelValue: '2026-11-22' }),
          h(CampoData, { name: 'nascimento', modelValue: '1990-05-07' }),
          h(CampoHora, { name: 'inicio', modelValue: '14:30' }),
          h(SeletorData, { name: 'sessao', modelValue: '2026-12-01' }),
          h(SeletorMes, { name: 'competencia', modelValue: '2026-11' }),
          h(SeletorAno, { name: 'exercicio', modelValue: '2026' }),
          h(CampoPeriodo, { name: 'vigencia' }),
          h(SeletorPeriodo, { name: 'periodo', modelValue: { inicio: '2026-11-10', fim: '2026-11-20' } }),
          h(CampoIntervaloHoras, { name: 'expediente', modelValue: { inicio: '08:00', fim: '18:00' } })
        ])
    }))
    await assentar()
    const dados = new FormData(document.getElementById('form-datas'))
    expect(dados.get('dia')).toBe('2026-11-22')
    expect(dados.get('nascimento')).toBe('1990-05-07')
    expect(dados.get('inicio')).toBe('14:30')
    expect(dados.get('sessao')).toBe('2026-12-01')
    expect(dados.get('competencia')).toBe('2026-11')
    expect(dados.get('exercicio')).toBe('2026')
    expect([dados.get('vigencia_inicio'), dados.get('vigencia_fim')]).toEqual(['', ''])
    expect([dados.get('periodo_inicio'), dados.get('periodo_fim')]).toEqual(['2026-11-10', '2026-11-20'])
    expect([dados.get('expediente_inicio'), dados.get('expediente_fim')]).toEqual(['08:00', '18:00'])
    expect([...dados.values()].join(' ')).not.toMatch(/undefined/)
  })

  it('V8-CMP-030: o seletor de data abre o calendário fora da página', async () => {
    const seletor = montar(SeletorData, { props: { modelValue: '2026-11-22', open: true, rotulo: 'Data' } })
    await assentar()
    const conteudo = document.querySelector('.v8-seletor-data')
    expect(conteudo).not.toBeNull()
    expect(seletor.element.contains?.(conteudo)).not.toBe(true)
    expect(conteudo.querySelector('[data-value="2026-11-22"]').hasAttribute('data-selected')).toBe(true)
  })

  it('V8-DS-017: a ilha ds-datas mostra os componentes de data e hora', async () => {
    expect(Object.hasOwn(ilhas, 'ds-datas')).toBe(true)
    const ilha = montar(DsDatas)
    await assentar()
    ;[Calendario, CalendarioPeriodo, CampoData, CampoPeriodo, SeletorData, SeletorPeriodo, CampoHora,
      CampoIntervaloHoras, SeletorMes, SeletorMeses, SeletorAno, SeletorAnos].forEach(componente => {
      expect(ilha.findComponent(componente).exists(), componente.__name).toBe(true)
    })
  })
})
