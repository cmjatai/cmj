<template>
  <div>
    <div class="container">
      <div class="row">
        <div class="col-md-3">
          <model-select @change="value => despesa.orgaoselected=value"
            class="form-opacity d-flex w-100"
            app="loa"
            model="orgao"
            choice="__str__"
            ordering="codigo"
            ref="orgaoSelect"
            :required="false"
            :extra_query="`&loa=${loa}`"
            ></model-select>
        </div>
        <div class="col-md-3">
          <model-select @change="value => despesa.unidadeselected=value"
            class="form-opacity d-flex w-100"
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
          <model-select @change="value => despesa.funcaoselected=value"
            class="form-opacity d-flex w-100"
            app="loa"
            model="funcao"
            choice="__str__"
            ordering="codigo"
            ref="funcaoSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
        </div>
        <div class="col-md-3">
          <model-select @change="value => despesa.subfuncaoselected=value"
            class="form-opacity d-flex w-100"
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
          <model-select @change="value => despesa.programaselected=value"
            class="form-opacity d-flex w-100"
            app="loa"
            model="programa"
            choice="__str__"
            ordering="codigo"
            ref="programaSelect"
            :required="false"
            :extra_query="`${qs_loa}`"
            ></model-select>
        </div>
        <div class="col-md-3">
          <b-form-select v-model="despesa.agrupamentoselected" :options="agrupamentos" :select-size="1"/>
        </div>
      </div>
      <div class="row">
        <div class="col-12 mt-3 bg-white p-3">
          <DoughnutChart v-if="chartData" :height="height" :chartDataUser="chartData"/>
        </div>
      </div>
    </div>
    <resize-observer @notify="handleResize" />
  </div>
</template>

<script>
import ModelSelect from '@/components/selects/ModelSelect.vue'
import DoughnutChart from '@/components/charts/DoughnutChart'

export default {
  name: 'LoaDetail',
  components: {
    DoughnutChart,
    ModelSelect
  },
  data () {
    return {
      loa: this.$route.params.pkloa,
      chartData: null,
      height: 600,
      despesa: {
        orgaoselected: null,
        unidadeselected: null,
        funcaoselected: null,
        subfuncaoselected: null,
        programaselected: null,
        agrupamentoselected: 'orgao'
      },
      agrupamentos: {
        orgao: 'Órgãos',
        unidade: 'Unidades Orçamentárias',
        funcao: 'Funções',
        subfuncao: 'SubFunções',
        programa: 'Programas'
      }
    }
  },
  computed: {
    qs_loa: function () {
      const value = this.loa
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
    }
  },
  methods: {
    handleResize () {
      const h = window.innerHeight * 0.85
      if (h !== this.height) {
        this.height = h
      }
      /* if (this.chartData && this.chartData.labels.length > 0) {
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
        agrupamento: t.despesa.agrupamentoselected
      }
      t.$nextTick()
        .then(() => {
          t.utils.postModelAction('loa', 'loa', t.loa, 'despesas_agrupadas', formFilter)
            .then((response) => {
              let labels = []
              let cor = t.build_colors(response.data.length)
              let data = []
              _.each(response.data, function (item, idx) {
                labels.push(item.especificacao)
                data.push(item.vm)
              })
              let chartData = {
                labels,
                datasets: [
                  {
                    backgroundColor: cor,
                    data
                  }
                ]
              }
              if (t.chartData === null) {
                t.chartData = chartData
                return
              }
              t.$set(t.chartData, 'labels', labels)
              t.$set(t.chartData.datasets, 0, {
                backgroundColor: cor,
                data
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
      const letters = '0123456789ABCDEF'

      const colors = []
      for (let x = 0; x < n; x++) {
        let color = '#'
        for (let y = 0; y < 6; y++) {
          color += letters[Math.floor(Math.random() * 16)]
        }
        colors.push(color)
      }
      return colors
    }
  },
  mounted: function () {
    this.fetch()
  }
}
</script>
