<template>
  <div class="vue-loa-detail">
    <div class="container" v-if="!loa.ano || !chartDataLoa">
      <strong class="d-block mx-5 my-5">Carregando Dados Gráficos...</strong>
    </div>
    <div class="container" v-if="loa.ano && chartDataLoa">
      <strong class="d-block mx-3 my-2">Utilize os filtros abaixo e/ou aplique agrupamentos para visões diferentes</strong>
      <div class="row c-fields">
        <div class="col-md-3">
          Órgãos
          <model-select @change="value => despesa.orgaoselected=value"
            v-model="despesa.orgaoselected"
            app="loa"
            model="orgao"
            choice="__str__"
            ordering="codigo"
            ref="orgaoSelect"
            :required="false"
            :extra_query="`&loa=${qs_loa}`"
            ></model-select>
          Unidades Orçamentárias
          <model-select @change="value => despesa.unidadeselected=value"
            v-model="despesa.unidadeselected"
            app="loa"
            model="unidadeorcamentaria"
            choice="__str__"
            ordering="codigo"
            ref="unidadeSelect"
            :required="false"
            :extra_query="`${qs_loa}${qs_orgao}`"
            ></model-select>
        </div>
        <div class="col-md-3">
          Funções
          <model-select @change="value => despesa.funcaoselected=value"
            v-model="despesa.funcaoselected"
            app="loa"
            model="funcao"
            choice="__str__"
            ordering="codigo"
            ref="funcaoSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
          Subfunções
          <model-select @change="value => despesa.subfuncaoselected=value"
            v-model="despesa.subfuncaoselected"
            app="loa"
            model="subfuncao"
            choice="__str__"
            ordering="codigo"
            ref="subfuncaoSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
        </div>
        <div class="col-md-3">
          Programas
          <model-select @change="value => despesa.programaselected=value"
            v-model="despesa.programaselected"
            app="loa"
            model="programa"
            choice="__str__"
            ordering="codigo"
            ref="programaSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
          Ações
          <model-select @change="value => despesa.acaoselected=value"
            v-model="despesa.acaoselected"
            app="loa"
            model="acao"
            choice="__str__"
            ordering="codigo"
            ref="acaoSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
        </div>
        <div class="col-md-1">
        </div>
        <div class="col-md-2 c-groups">
          <div class="">
            <strong>Agrupamentos</strong>
            <b-form-select v-model="despesa.agrupamentoselected" :options="agrupamentos__options" :select-size="1"/>
          </div>
          <div class="row">
            <div class="col-6">
              <strong>Máximo de Itens</strong>
              <b-form-select v-model="despesa.itensselected" :options="itens" :select-size="1"/>
            </div>
            <div class="col-6">
              <strong>Histograma</strong>
              <b-form-select v-model="barchart_max_items__select" :options="itens_hist" :select-size="1"/>
            </div>
          </div>
          <div class="col mt-1 text-right">
            <b-button class="bg-secondary" size="sm" @click="clearFilters(event)">Limpar Pesquisa</b-button>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-12 container-doughnut p-3 mt-3">
          <DoughnutChart v-if="chartDataLoa" :height="height" :plugins="pluginsDun" :chartDataUser="chartDataLoa"/>

          <b-table striped hover class="local_table" :items="despesas_agrupadas_table"></b-table>

        </div>

        <div class="col-12 mt-3" v-html="loa.yaml_obs && loa.yaml_obs.GRAFICO_DESPESAS_MATERIA ? loa.yaml_obs.GRAFICO_DESPESAS_MATERIA : ''"></div>

        <div class="col-12 container-barchart p-3 mt-3" v-if="chartDataHist">
          <div class="btn-barchart-left" @click="clickSlice(-1, 'hist')"><i class="fa fa-chevron-left"></i></div>
          <div class="btn-barchart-right" @click="clickSlice(1, 'hist')"><i class="fa fa-chevron-right"></i></div>
          <BarChart :plugins="pluginsBar" :chartDataUser="chartDataHist" cssClasses="barchart-component"/>
        </div>
        <div class="col-12 container-barchart p-3 mt-3" v-if="chartDataExec">
          <div class="btn-barchart-left" @click="clickSlice(-1, 'exec')"><i class="fa fa-chevron-left"></i></div>
          <div class="btn-barchart-right" @click="clickSlice(1, 'exec')"><i class="fa fa-chevron-right"></i></div>
          <BarChart :plugins="pluginsExec" :chartDataUser="chartDataExec" cssClasses="barchart-2"/>
          <div class="fonte small pt-5">
            FONTE: Os dados são extraídos no período noturno dos portais de transparência do
              <a href="http://prefeituradejatai.sigepnet.com.br">Poder Executivo</a> e do
              <a href="http://camaradejatai.sigepnet.com.br">Poder Legislativo</a>, portanto,
              os valores se referem a movimentação do dia anterior.
              Os valores extraídos são sempre os divulgados como "Valor Bruto",
              não sendo possível atualmente, possuir uma coluna com o "Valor Líquido"
              por esta, apesar de estar presente nos dados humanamente visíveis,
              não está nos dados abertos no format CSV.
              A totalização dos valores pode possuir variações de 1 a 2% com o mostrado nos portais de transparência.
              Abaixo uma listagem de cada Órgão, com sua última data e último código de despesa extraída.
              <ul>
                <li v-for="(data, key) in data_exec" :key="key" >
                  {{ data[6] }} - {{ data[5] }} - {{ data[0] }}-{{ data[1] }}
                </li>
              </ul>
          </div>
        </div>
      </div>
    </div>
    <resize-observer @notify="handleResize" />
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'
import DoughnutChart from '@/components/charts/DoughnutChart'
import BarChart from '@/components/charts/BarChart'
import YAML from 'js-yaml' // eslint-disable-line
// import { parse, stringify } from 'yaml' // eslint-disable-line

export default {
  name: 'LoaDetail',
  components: {
    BarChart,
    DoughnutChart,
    ModelSelect
  },
  data () {
    return {
      loa: {
        id: this.$route.params.pkloa
      },
      chartDataLoa: null,
      chartDataHist: null,
      chartDataExec: null,
      data_exec: null,
      height: 550,
      pluginsExec: [{
        title: {
          display: true,
          text: ''
        }
      }],
      pluginsBar: [{
        title: {
          display: true,
          text: ''
        }
      }],
      pluginsDun: [{
        title: {
          display: true,
          text: ''
        }
      }],
      despesas_agrupadas: [
      ],
      despesa: {
        orgaoselected: null,
        unidadeselected: null,
        funcaoselected: null,
        subfuncaoselected: null,
        programaselected: null,
        acaoselected: null,
        agrupamentoselected: 'funcao',
        itensselected: 20
      },
      filters: [
        'orgaoselected',
        'unidadeselected',
        'funcaoselected',
        'subfuncaoselected',
        'programaselected',
        'acaoselected'
      ],
      agrupamentos: {
        orgao: 'Órgãos',
        unidade: 'Unidades Orçamentárias',
        funcao: 'Funções',
        subfuncao: 'SubFunções',
        programa: 'Programas',
        acao: 'Ações',
        natureza_1: 'Natureza - Nível 1',
        natureza_2: 'Natureza - Nível 2',
        natureza_3: 'Natureza - Nível 3',
        natureza_4: 'Natureza - Nível 4',
        natureza_5: 'Natureza - Nível 5',
        fonte: 'Fonte de Recurso'
      },
      tipos_agrups: [
        'orgao',
        'unidade',
        'funcao',
        'subfuncao',
        'programa',
        'acao',
        'natureza_1',
        'natureza_2',
        'natureza_3',
        'natureza_4',
        'natureza_5',
        'fonte'
      ],
      itens: [
        { value: 5, text: '05 Maiores' },
        { value: 10, text: '10 Maiores' },
        { value: 15, text: '15 Maiores' },
        { value: 20, text: '20 Maiores' },
        { value: 25, text: '25 Maiores' },
        { value: 999, text: 'Todos os Itens' }
      ],
      itens_hist: [
        { value: 5, text: '05 Itens' },
        { value: 10, text: '10 Itens' },
        { value: 15, text: '15 Itens' },
        { value: 20, text: '20 Itens' }
      ],
      barchart_exec_offset: 0,
      barchart_exec_length: 0,

      barchart_offset: 0,
      barchart_length: 0,
      barchart_max_items__select: 5,
      barchart_max_items: 5,
      barchart_colors: this.build_colors(20, 'a0')
    }
  },
  computed: {
    qs_loa: function () {
      const value = this.loa.id
      return value ? `&loa=${value}&despesa_set__isnull=False` : ''
    },
    qs_orgao: function () {
      const value = this.despesa.orgaoselected
      return value && value.id ? `&orgao=${value.id}` : ''
    },
    agrupamentos__options: function () {
      const t = this
      const groups = []
      _.forOwn(t.agrupamentos, function (text, value) {
        groups.push({ text, value })
      })
      return groups
    },
    despesas_agrupadas_table: function () {
      const t = this
      const table = []
      let table_base = _.orderBy(_.filter(t.despesas_agrupadas, (o) => o.alt), ['codigo'])

      _.each(table_base, function (item, idx) {
        table.push({
          'Código': item.codigo,
          'Especificação': item.especificacao,
          'Valor no Orçamento': item.vm_str,
          'Emendas Imposititivas': item.alt_str,
          'Saldo Final': item.saldo_str
        })
      })
      return table
    }
  },
  watch: {
    barchart_max_items__select: {
      handler (nv, ov) {
        this.barchart_exec_offset = 0

        this.barchart_offset = 0
        this.barchart_max_items = Number(nv)
        this.fetch('', 1)
      }
    },
    'despesa.orgaoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('unidade')) {
                t.despesa.agrupamentoselected = 'unidade'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.unidadeselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('funcao')) {
                t.despesa.agrupamentoselected = 'funcao'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.funcaoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('subfuncao')) {
                t.despesa.agrupamentoselected = 'subfuncao'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.subfuncaoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('programa')) {
                t.despesa.agrupamentoselected = 'programa'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.programaselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('acao')) {
                t.despesa.agrupamentoselected = 'acao'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.acaoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              if (t.tipos_agrups.indexOf(t.despesa.agrupamentoselected) < t.tipos_agrups.indexOf('natureza_1')) {
                t.despesa.agrupamentoselected = 'natureza_5'
              }
              t.fetch()
            })
        }
      }
    },
    'despesa.agrupamentoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        if ((ov || nv) && ov !== nv) {
          t.$nextTick()
            .then(function () {
              t.fetch()
            })
        }
      }
    },
    'despesa.itensselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        t.$nextTick()
          .then(function () {
            if ((ov || nv) && ov !== nv) {
              t.fetch()
            }
          })
      }
    }
  },
  methods: {
    clearFilters (event) {
      const t = this
      t.despesa = {
        orgaoselected: null,
        unidadeselected: null,
        funcaoselected: null,
        subfuncaoselected: null,
        programaselected: null,
        acaoselected: null,
        agrupamentoselected: 'funcao',
        itensselected: 20
      }
    },
    clickSlice (value, grafico) {
      if (grafico === 'hist') {
        if (
          (value === -1 && this.barchart_offset > 0) ||
          (value === 1 && this.barchart_offset + this.barchart_max_items < this.barchart_length)
        ) {
          this.barchart_offset += value
          this.fetch('', 1)
        }
      } else {
        if (
          (value === -1 && this.barchart_exec_offset > 0) ||
          (value === 1 && this.barchart_exec_offset + this.barchart_max_items < this.barchart_exec_length)
        ) {
          this.barchart_exec_offset += value
          this.fetch('', 1)
        }
      }
    },
    handleResize () {
      /* const h = window.innerHeight * 0.65
      if (h !== this.height) {
        this.height = h
      }
      if (this.chartDataLoa && this.chartDataLoa.labels.length > 0) {
        let hlabels = h / this.chartDataLoa.labels.length
        if (hlabels < 50) {
          this.height = this.chartDataLoa.labels.length * 50
        }
      } */
    },
    fetch (recursive = '', hist = 0) {
      const t = this
      const formFilter = {
        orgao: t.despesa.orgaoselected ? t.despesa.orgaoselected.codigo : null,
        unidade: t.despesa.unidadeselected ? `${t.despesa.unidadeselected.codigo}/${t.despesa.unidadeselected.orgao}` : null,
        funcao: t.despesa.funcaoselected ? t.despesa.funcaoselected.codigo : null,
        subfuncao: t.despesa.subfuncaoselected ? t.despesa.subfuncaoselected.codigo : null,
        programa: t.despesa.programaselected ? t.despesa.programaselected.codigo : null,
        acao: t.despesa.acaoselected ? t.despesa.acaoselected.codigo : null,
        agrupamento: recursive === '' ? t.despesa.agrupamentoselected : recursive,
        itens: t.despesa.itensselected
      }
      t.$nextTick()
        .then(() => {
          if (hist !== 0) {
            return this
          }
          // t.barchart_max_items = formFilter.itens
          t.barchart_offset = 0
          t.barchart_exec_offset = 0
          formFilter.hist = hist
          t.utils.postModelAction('loa', 'loa', t.loa.id, 'despesas_agrupadas', formFilter)
            .then((response) => {
              let labels = []
              let cor = t.build_colors(response.data.length)
              let data = []
              _.each(response.data, function (item, idx) {
                labels.push(`${item.vm_str} / ${item.codigo}-${item.especificacao}`)
                data.push(item.vm)
              })
              const chartDataLoa = {
                labels,
                datasets: [
                  {
                    data,
                    backgroundColor: cor,
                    hoverOffset: 50
                  }
                ]
              }
              if (t.chartDataLoa === null) {
                t.chartDataLoa = chartDataLoa
                return
              }
              t.$set(t.chartDataLoa, 'labels', labels)
              t.$set(t.chartDataLoa.datasets, recursive === '' ? 0 : 1, {
                data,
                backgroundColor: cor,
                hoverOffset: 50
              })

              const text = [
                `ORÇAMENTO DE ${t.loa.ano} DO MUNICÍPIO DE JATAÍ`
              ]
              const filters = []
              _.forOwn(t.despesa, function (value, key) {
                if (t.filters.includes(key) && value !== null) {
                  filters.push(value.especificacao)
                }
              })
              if (!_.isEmpty(filters)) {
                text.push(`FILTRADO POR: ${filters.join(' / ')}`)
              }
              text.push(`Orçamento das despesas agrupadas por: ${t.agrupamentos[formFilter.agrupamento]}`)
              if (_.isEmpty(data)) {
                text.push('Sem dados para mostrar')
              } else {
                text.push(`R$ ${response.data.length > 0 ? response.data[0].vm_soma : '0,00'}.`)
              }

              t.$set(t.pluginsDun, 0, {
                title: {
                  display: true,
                  text: text
                }
              })

              if (recursive === '') {
                // t.fetch('orgao')
              }
            })
            .then((response) => {
              this.handleResize()
            })
            .catch((response) => t.sendMessage(
              { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 }))
        })
        .then(() => {
          formFilter.hist = 1
          t.utils.postModelAction('loa', 'loa', t.loa.id, 'despesas_agrupadas', formFilter)
            .then((response) => {
              let labels = response.data.labels.slice(t.barchart_offset, t.barchart_offset + t.barchart_max_items)
              let cor = t.barchart_colors // t.build_colors(response.data.anos.length, 'a0')
              let datasets = []
              _.each(response.data.anos, function (label, idx) {
                let data = []
                if (idx === 0 && t.barchart_offset === 0) {
                  t.barchart_length = response.data.pre_datasets[label].length
                }
                _.each(response.data.pre_datasets[label].slice(t.barchart_offset, t.barchart_offset + t.barchart_max_items), function (itemD, idd) {
                  data.push(itemD.vm)
                })
                datasets.push({
                  label,
                  data,
                  backgroundColor: cor[idx]
                })
              })
              let chartDataHist = {
                labels,
                datasets
              }
              if (t.chartDataHist === null) {
                t.chartDataHist = chartDataHist
                return
              }
              const text = [
                'HISTOGRAMA DO ORÇAMENTO DO MUNICÍPIO DE JATAÍ'
              ]
              const filters = []
              _.forOwn(t.despesa, function (value, key) {
                if (t.filters.includes(key) && value !== null) {
                  filters.push(value.especificacao)
                }
              })
              if (!_.isEmpty(filters)) {
                text.push(`FILTRADO POR: ${filters.join(' / ')}`)
              }
              text.push(`Orçamento das despesas agrupadas por: ${t.agrupamentos[formFilter.agrupamento]}`)

              t.$set(t.chartDataHist, 'labels', labels)
              t.$set(t.chartDataHist, 'datasets', datasets)
              t.$set(t.pluginsBar, 0, {
                title: {
                  display: true,
                  text
                }
              })
            })
            .then((response) => {
              this.handleResize()
            })
            .catch((response) => t.sendMessage(
              { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 }))
        })
        .then(() => {
          /* formFilter.itens = 1000
          formFilter.hist = 0
          t.utils.postModelAction('loa', 'loa', t.loa.id, 'despesas_agrupadas', formFilter)
            .then((response) => {
              t.despesas_agrupadas = response.data
            }) */
        })
        .then(() => {
          t.utils.getModelAction('loa', 'loa', t.loa.id, 'despesas_executadas')
            .then((response) => {
              t.data_exec = response.data
              let cor = t.barchart_colors // t.build_colors(response.data.anos.length, 'a0')
              let labels = []
              let data_orc = []
              let data_exe = []
              let data_recorc = []
              _.each(response.data, function (item, idx) {
                labels.push(`${item[0]} - ${item[1]}`)
                data_orc.push(item[2])
                data_exe.push(item[3])
                data_recorc.push(item[4])
              })
              t.barchart_exec_length = labels.length
              labels = labels.slice(t.barchart_exec_offset, t.barchart_exec_offset + t.barchart_max_items)
              let datasets = [
                {
                  label: 'Despesas Orçamentárias',
                  data: data_orc.slice(t.barchart_exec_offset, t.barchart_exec_offset + t.barchart_max_items),
                  backgroundColor: cor[0]
                },
                {
                  label: 'Despesas Executadas',
                  data: data_exe.slice(t.barchart_exec_offset, t.barchart_exec_offset + t.barchart_max_items),
                  backgroundColor: cor[1]
                },
                {
                  label: 'Receita Arrecadada',
                  data: data_recorc.slice(t.barchart_exec_offset, t.barchart_exec_offset + t.barchart_max_items),
                  backgroundColor: cor[2]
                }
              ]
              let chartDataExec = {
                labels,
                datasets
              }
              if (t.chartDataExec === null) {
                t.chartDataExec = chartDataExec
                return
              }
              const text = [
                `ORÇAMENTO vs EXECUÇÃO - ${t.loa.ano}`
              ]
              t.$set(t.chartDataExec, 'labels', labels)
              t.$set(t.chartDataExec, 'datasets', datasets)
              t.$set(t.pluginsExec, 0, {
                title: {
                  display: true,
                  text
                }
              })
            })
            .then((response) => {
              this.handleResize()
            })
            .catch((response) => {
              // t.sendMessage(
              // { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 })
            })
        })
    },
    build_colors (n, alpha = '') {
      const colors = []
      if (n < 1) {
        return colors
      }

      let hue = Math.floor(Math.random() * 360)
      let delta = 0

      let hsl2rgb = (h, s, l, a = s * Math.min(l, 1 - l), f = (n, k = (n + h / 30) % 12) => l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1)) => [f(0), f(8), f(4)]
      let rgb2hex = (r, g, b) => '#' + [r, g, b].map(x => Math.round(x * 255).toString(16).padStart(2, 0)).join('')

      for (let x = 0; x < n; x++) {
        let hex = `${rgb2hex(...hsl2rgb(hue, Math.max(0.8, Math.random()), 0.4))}`
        delta = Math.random() * 30 + (hue < 150 ? 50 : 25)
        // console.log('Delta', delta, 'Hue:', hue)
        hue = (hue + delta) % 360
        colors.push(`${hex}${alpha}`)
      }
      return colors
    },
    build_colors_hsl (n) {
      const colors = []
      if (n < 1) {
        return colors
      }
      let hue = Math.floor(Math.random() * 360)
      let delta = 0
      for (let x = 0; x < n; x++) {
        let color = 'hsl( ' + hue + ', 100%, 40%)'

        delta = Math.random() * 30 + (hue < 150 ? 50 : 25)
        // console.log('Delta', delta, 'Hue:', hue)
        hue = (hue + delta) % 360
        colors.push(color)
      }
      return colors
    },
    build_colors_random (n) {
      const letters = '0123456789ABCDEF'

      const colors = []
      for (let x = 0; x < n; x++) {
        let color = '#'
        for (let y = 0; y < 6; y++) {
          color += letters[Math.floor(Math.random() * (y % 2 === 0 ? 14 : 16))]
        }
        colors.push(color)
      }
      return colors
    }
  },
  mounted: function () {
    const t = this
    t.$nextTick()
      .then(() => {
        t.utils.getModel('loa', 'loa', t.loa.id)
          .then((response) => {
            const yaml_obs = YAML.load(response.data.yaml_obs)
            response.data.yaml_obs = yaml_obs
            t.loa = response.data
            // t.fetch()
          })
      })
  }
}
</script>
<style lang="scss" scoped>
  $mp: 3px;
  .vue-loa-detail {
    margin-bottom: 2em;
  }
  [class^=col] {
    padding-left: $mp;
    padding-right: $mp;
  }
  .col-md-1 {
    flex: 0 0 7.5%;
    max-width: 7.5%;
  }
  .colwithbuttonclean {
    margin-left: -$mp;
    margin-right: -$mp;
    align-items: center;
    .acaoselected {
      flex: 1 2 auto;
    }
    button {
      text-wrap: nowrap;
    }
  }
  .c-fields {
  }
  .c-groups {
    font-size: 80%;
    padding-top: $mp * 2;
    /*position: fixed;
    bottom: 0;
    right: 0;
    background-color: #00ff00;
    z-index: 1;
    padding: 10px;
    opacity: 0.6;
    &:hover {
      opacity: 1;
    }*/
    .custom-select {
      font-size: 100%;
      padding: $mp;
      height: auto;
    }
    .btn {
      padding: $mp $mp * 2;
      line-height: 1;
    }
  }
  .container-doughnut, .container-barchart {
    position: relative;
    background-color: #fffc;
    .btn-barchart-left, .btn-barchart-right {
      color: #3232c0;
      position:absolute;
      z-index: 1;
      left: 0;
      font-size: 300%;
      top: 40%;
      padding: 0.5rem;
      opacity: 0.4;
      display: flex;
      align-items: center;
      cursor: pointer;
      &:hover {
        transition: all 0.4s ease;
        opacity: 1;
        font-size: 350%;
      }
    }
    .btn-barchart-right {
      left: auto;
      right: 0;
    }
    .fonte {
      font-family: 'Courier New', Courier, monospace;
      font-size: 80%;
      a {
        text-decoration: underline;
      }
    }
  }
  .local_table {
    td:nth-child(n + 3) {
      text-align: right;
    }
  }
</style>
