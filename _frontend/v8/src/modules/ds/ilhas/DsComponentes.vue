<template>
  <div class="grid gap-8 lg:grid-cols-2">
    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Abas</code>
      <Abas
        v-model="aba"
        rotulo="Abas de exemplo"
        :itens="ABAS"
      >
        <template #geral>
          <p>Painel geral.</p>
        </template>
        <template #historico>
          <p>Painel de histórico.</p>
        </template>
        <template #anexos>
          <p>Painel de anexos.</p>
        </template>
      </Abas>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Sanfona</code>
      <Sanfona
        v-model="secao"
        :itens="SECOES"
      >
        <template #dados>
          <p>Dados da seção.</p>
        </template>
        <template #tramitacao>
          <p>Tramitação da seção.</p>
        </template>
        <template #votacao>
          <p>Votação da seção.</p>
        </template>
      </Sanfona>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Dica, Popover, MenuSuspenso</code>
      <div class="v8-barra-acoes">
        <Dica texto="Texto curto da dica">
          <button
            type="button"
            class="v8-btn"
          >
            Dica
          </button>
        </Dica>
        <Popover titulo="Popover">
          <template #gatilho>
            <button
              type="button"
              class="v8-btn"
            >
              Popover
            </button>
          </template>
          <template #default="{ fechar }">
            <p class="mb-3">
              Conteúdo do popover.
            </p>
            <button
              type="button"
              class="v8-btn v8-btn-primario"
              @click="fechar"
            >
              Aplicar
            </button>
          </template>
        </Popover>
        <MenuSuspenso
          rotulo="Menu suspenso"
          :itens="ACOES"
          @selecionar="valor => (acao = valor)"
        />
      </div>
      <p
        class="text-sm text-texto-suave"
        data-ds-acao-escolhida
      >
        {{ acao }}
      </p>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Selecao</code>
      <Selecao
        v-model="bairro"
        rotulo="Bairro"
        name="bairro"
        :opcoes="BAIRROS"
        placeholder="Escolha o bairro"
      />
      <Selecao
        rotulo="Desabilitada"
        :opcoes="BAIRROS"
        placeholder="Desabilitada"
        disabled
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">CaixaMarcacao</code>
      <CaixaMarcacao
        v-model="aceito"
        rotulo="Marcada"
      />
      <CaixaMarcacao
        v-model="parcial"
        rotulo="Indeterminada"
      />
      <CaixaMarcacao rotulo="Desmarcada" />
      <CaixaMarcacao
        rotulo="Desabilitada"
        disabled
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">GrupoOpcoes, Chave</code>
      <GrupoOpcoes
        v-model="turno"
        rotulo="Turno"
        orientacao="horizontal"
        :opcoes="TURNOS"
      />
      <Chave
        v-model="avisar"
        rotulo="Ligada"
      />
      <Chave rotulo="Desligada" />
      <Chave
        rotulo="Desabilitada"
        disabled
      />
    </div>
  </div>
</template>

<script setup>
// Ilha `ds-componentes` da vitrine (V8-DS-014): os componentes base de componentes.md, com dados
// de amostra. Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { ref } from 'vue'
import Abas from '~@/componentes/Abas.vue'
import CaixaMarcacao from '~@/componentes/CaixaMarcacao.vue'
import Chave from '~@/componentes/Chave.vue'
import Dica from '~@/componentes/Dica.vue'
import GrupoOpcoes from '~@/componentes/GrupoOpcoes.vue'
import MenuSuspenso from '~@/componentes/MenuSuspenso.vue'
import Popover from '~@/componentes/Popover.vue'
import Sanfona from '~@/componentes/Sanfona.vue'
import Selecao from '~@/componentes/Selecao.vue'
import { BAIRROS as NOMES_DE_BAIRRO } from '~@/modules/ds/amostras'

// 4. State & Refs
const ABAS = [
  { valor: 'geral', rotulo: 'Geral' },
  { valor: 'historico', rotulo: 'Histórico' },
  { valor: 'anexos', rotulo: 'Anexos' },
  { valor: 'bloqueada', rotulo: 'Desabilitada', desabilitado: true }
]
const SECOES = [
  { valor: 'dados', titulo: 'Dados' },
  { valor: 'tramitacao', titulo: 'Tramitação' },
  { valor: 'votacao', titulo: 'Votação' }
]
const ACOES = [
  { titulo: 'Registro' },
  { valor: 'editar', rotulo: 'Editar' },
  { valor: 'duplicar', rotulo: 'Duplicar' },
  { valor: 'arquivar', rotulo: 'Arquivar', desabilitado: true },
  { separador: true },
  { valor: 'excluir', rotulo: 'Excluir', perigo: true }
]
const BAIRROS = NOMES_DE_BAIRRO.map(nome => ({ valor: nome, rotulo: nome }))
const TURNOS = [
  { valor: 'manha', rotulo: 'Manhã' },
  { valor: 'tarde', rotulo: 'Tarde' },
  { valor: 'noite', rotulo: 'Noite', desabilitado: true }
]

const aba = ref('geral')
const secao = ref('dados')
const acao = ref('')
const bairro = ref(undefined)
const aceito = ref(true)
const parcial = ref('indeterminate')
const turno = ref('tarde')
const avisar = ref(true)
</script>
