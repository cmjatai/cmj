<template>
  <div class="loa-detail">
    <div class="container">
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
            <b-form-select v-model="despesa.agrupamentoselected" :options="agrupamentos" :select-size="1"/>
          </div>
          <div class="">
            <strong>Máximo de Itens</strong>
            <b-form-select v-model="despesa.itensselected" :options="itens" :select-size="1"/>
          </div>
          <div class="col mt-1 text-right">
            <b-button class="bg-secondary" size="sm" @click="clearFilters(event)">Limpar Pesquisa</b-button>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-12 mt-3 bg-white p-3">
          <DoughnutChart v-if="chartData" :height="height" :plugins="plugins" :chartDataUser="chartData"/>
        </div>
        <div class="col-12 mt-3 " v-html="loa.yaml_obs && loa.yaml_obs.GRAFICO_DESPESAS_MATERIA ? loa.yaml_obs.GRAFICO_DESPESAS_MATERIA : ''"></div>
      </div>
    </div>
    <resize-observer @notify="handleResize" />
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'
import DoughnutChart from '@/components/charts/DoughnutChart'
import YAML from 'js-yaml' // eslint-disable-line
// import { parse, stringify } from 'yaml' // eslint-disable-line

export default {
  name: 'LoaDetail',
  components: {
    DoughnutChart,
    ModelSelect
  },
  data () {
    return {
      loa: {
        id: this.$route.params.pkloa
      },
      chartData: null,
      height: 400,
      plugins: [{
        title: {
          display: true,
          text: ''
        }
      }],
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
        natureza_5: 'Natureza - Nível 5'
      },
      itens: {
        5: '05 Maiores',
        10: '10 Maiores',
        15: '15 Maiores',
        20: '20 Maiores',
        25: '25 Maiores',
        0: 'Todos os Itens'
      }
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
    }
  },
  watch: {
    'despesa.orgaoselected': {
      deep: true,
      immediate: true,
      handler (nv, ov) {
        const t = this
        t.$nextTick()
          .then(function () {
            if ((ov || nv) && ov !== nv) {
              t.$refs.unidadeSelect.fetch()
              t.fetch()
            }
          })
      }
    },
    'despesa.unidadeselected': {
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
    },
    'despesa.funcaoselected': {
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
    },
    'despesa.subfuncaoselected': {
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
    },
    'despesa.programaselected': {
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
    },
    'despesa.acaoselected': {
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
    },
    'despesa.agrupamentoselected': {
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
    handleResize () {
      /* const h = window.innerHeight * 0.65
      if (h !== this.height) {
        this.height = h
      }
      if (this.chartData && this.chartData.labels.length > 0) {
        let hlabels = h / this.chartData.labels.length
        if (hlabels < 50) {
          this.height = this.chartData.labels.length * 50
        }
      } */
    },
    fetch () {
      const t = this
      const formFilter = {
        orgao: t.despesa.orgaoselected ? t.despesa.orgaoselected.id : null,
        unidade: t.despesa.unidadeselected ? t.despesa.unidadeselected.id : null,
        funcao: t.despesa.funcaoselected ? t.despesa.funcaoselected.id : null,
        subfuncao: t.despesa.subfuncaoselected ? t.despesa.subfuncaoselected.id : null,
        programa: t.despesa.programaselected ? t.despesa.programaselected.id : null,
        acao: t.despesa.acaoselected ? t.despesa.acaoselected.id : null,
        agrupamento: t.despesa.agrupamentoselected,
        itens: t.despesa.itensselected
      }
      t.$nextTick()
        .then(() => {
          t.utils.postModelAction('loa', 'loa', t.loa.id, 'despesas_agrupadas', formFilter)
            .then((response) => {
              let labels = []
              let cor = t.build_colors(response.data.length)
              let data = []
              _.each(response.data, function (item, idx) {
                labels.push(`${item.vm_str} / ${item.codigo}-${item.especificacao}`)
                data.push(item.vm)
              })
              let chartData = {
                labels,
                datasets: [
                  {
                    data,
                    backgroundColor: cor,
                    hoverOffset: 50
                  }
                ]
              }
              if (t.chartData === null) {
                t.chartData = chartData
                return
              }
              t.$set(t.chartData, 'labels', labels)
              t.$set(t.chartData.datasets, 0, {
                data,
                backgroundColor: cor,
                hoverOffset: 50
              })
              t.$set(t.plugins, 0, {
                title: {
                  display: true,
                  text: `ORÇAMENTO NO PROJETO ORIGINAL: R$ ${response.data.length > 0 ? response.data[0].vm_soma : '0,00'}. Despesas agrupadas por: ${t.agrupamentos[formFilter.agrupamento]}`
                }
              })
            })
            .then((response) => {
              this.handleResize()
            })
            .catch((response) => t.sendMessage(
              { alert: 'danger', message: 'Não foi possível recuperar a lista...', time: 5 }))
        })
    },
    build_colors (n) {
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
        colors.push(hex)
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
    t.fetch()

    t.$nextTick()
      .then(() => {
        t.utils.getModel('loa', 'loa', t.loa.id)
          .then((response) => {
            const yaml_obs = YAML.load(response.data.yaml_obs)
            response.data.yaml_obs = yaml_obs
            t.loa = response.data
          })
      })
  }
}
</script>
<style lang="scss" scoped>
  .loa-detail {
    margin-bottom: 2em;
  }
  $mp: 3px;
  [class^=col] {
    padding-left: $mp;
    padding-right: $mp;
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
</style>
