<template>
  <div class="grid gap-8 lg:grid-cols-2">
    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Calendario</code>
      <Calendario
        v-model="dia"
        rotulo="Data da sessão"
      />
      <p class="text-sm text-texto-suave">
        {{ dia || 'sem data' }}
      </p>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">CalendarioPeriodo</code>
      <CalendarioPeriodo v-model="periodo" />
      <p class="text-sm text-texto-suave">
        {{ periodo.inicio || '…' }} a {{ periodo.fim || '…' }}
      </p>
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">CampoData, CampoPeriodo, CampoHora, CampoIntervaloHoras</code>
      <CampoData
        v-model="dia"
        rotulo="Data"
      />
      <CampoPeriodo
        v-model="periodo"
        rotulo="Período"
      />
      <CampoHora
        v-model="hora"
        rotulo="Hora"
      />
      <CampoIntervaloHoras
        v-model="expediente"
        rotulo="Expediente"
      />
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">SeletorData, SeletorPeriodo</code>
      <SeletorData
        v-model="dia"
        rotulo="Data"
      />
      <SeletorPeriodo
        v-model="periodo"
        rotulo="Período"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">SeletorMes, SeletorMeses</code>
      <SeletorMes
        v-model="competencia"
        rotulo="Competência"
      />
      <SeletorMeses
        v-model="meses"
        rotulo="Meses"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">SeletorAno, SeletorAnos</code>
      <SeletorAno
        v-model="exercicio"
        rotulo="Exercício"
      />
      <SeletorAnos
        v-model="anos"
        rotulo="Anos"
      />
    </div>
  </div>
</template>

<script setup>
// Ilha `ds-datas` da vitrine (V8-DS-017): os componentes de data e hora de componentes.md, com
// valores de amostra em texto ISO. Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { ref } from 'vue'
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

// 4. State & Refs
const dia = ref('2026-11-22')
const periodo = ref({ inicio: '2026-11-10', fim: '2026-11-20' })
const hora = ref('14:30')
const expediente = ref({ inicio: '08:00', fim: '18:00' })
const competencia = ref('2026-11')
const meses = ref({ inicio: '2026-01', fim: '2026-03' })
const exercicio = ref('2026')
const anos = ref({ inicio: '2025', fim: '2028' })
</script>
