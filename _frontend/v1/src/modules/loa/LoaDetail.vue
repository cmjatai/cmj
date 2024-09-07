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
      </div>
      <div class="row">
        <div class="col-12">
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
        unidadeselected: null
      }
    }
  },
  computed: {
    qs_loa: function () {
      const value = this.loa
      return value ? `&loa=${value}` : ''
    },
    qs_orgao: function () {
      const value = this.despesa.orgaoselected
      return value && value.id ? `&orgao=${value.id}` : ''
    }
  },
  watch: {
    'despesa.orgaoselected': function (nv, ov) {
      const t = this
      t.$nextTick()
        .then(function () {
          if (ov) {
            t.$refs.unidadeSelect.fetch()
          }
        })
    },
    'despesa.unidadeselected': function (nv, ov) {
    }
  },
  methods: {
    handleResize () {
      const h = window.innerHeight * 0.7
      if (h !== this.height) {
        this.height = h
      }
    },
    fetch () {

    }
  },
  mounted: function () {
    this.chartData = {
      labels: ['VueJs', 'EmberJs', 'ReactJs', 'AngularJs'],
      datasets: [
        {
          backgroundColor: ['#41B883', '#E46651', '#00D8FF', '#DD1B16'],
          data: [40, 20, 80, 10]
        }
      ]
    }
  }
}
</script>
