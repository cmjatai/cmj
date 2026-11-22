<template>
  <div class="grid gap-8 lg:grid-cols-2">
    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Rotulo, Alternador, GrupoAlternadores</code>
      <Rotulo para="ds-c-numero">
        Rótulo de campo
      </Rotulo>
      <div class="v8-barra-acoes">
        <Alternador
          v-model="negrito"
          rotulo="Negrito"
        >
          Negrito
        </Alternador>
        <GrupoAlternadores
          v-model="alinhamento"
          rotulo="Alinhamento"
          :itens="ALINHAMENTOS"
        />
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">Deslizante</code>
      <Deslizante
        v-model="volume"
        rotulo="Volume"
        :max="10"
      />
      <Deslizante
        v-model="faixa"
        rotulo="Faixa"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">CampoNumero, CampoCodigo</code>
      <CampoNumero
        id="ds-c-numero"
        v-model="valor"
        :formato="MOEDA"
        :passo="0.5"
      />
      <CampoCodigo
        v-model="codigo"
        rotulo="Código"
        :tamanho="6"
        numerico
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">CampoEtiquetas, GrupoEtiquetas</code>
      <CampoEtiquetas
        v-model="assuntos"
        rotulo="Assuntos"
        placeholder="Novo assunto"
      />
      <GrupoEtiquetas
        v-model="filtrosMarcados"
        rotulo="Filtros"
        selecao="multiple"
        removivel
        :itens="filtros"
        @remover="tirarFiltros"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">TextoEditavel, Avaliacao</code>
      <TextoEditavel
        v-model="titulo"
        rotulo="Título"
      />
      <Avaliacao
        v-model="nota"
        rotulo="Nota"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">SelecaoBusca, Autocompletar</code>
      <SelecaoBusca
        v-model="bairro"
        rotulo="Bairro"
        :opcoes="BAIRROS"
      />
      <Autocompletar
        v-model="cidade"
        rotulo="Cidade"
        placeholder="Cidade"
        :sugestoes="CIDADES"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">ListaOpcoes</code>
      <ListaOpcoes
        v-model="temas"
        rotulo="Temas"
        multipla
        :opcoes="TEMAS"
      />
    </div>
  </div>
</template>

<script setup>
// Ilha `ds-campos` da vitrine (V8-DS-015): os componentes de campo de componentes.md, com dados
// de amostra. Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { ref } from 'vue'
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
import { BAIRROS as NOMES_DE_BAIRRO } from '~@/modules/ds/amostras'

// 4. State & Refs
const ALINHAMENTOS = [
  { valor: 'esquerda', rotulo: 'Esquerda' },
  { valor: 'centro', rotulo: 'Centro' },
  { valor: 'direita', rotulo: 'Direita' }
]
const MOEDA = { style: 'currency', currency: 'BRL' }
const BAIRROS = NOMES_DE_BAIRRO.map(nome => ({ valor: nome, rotulo: nome }))
const CIDADES = ['Jataí', 'Rio Verde', 'Mineiros', 'Caiapônia', 'Goiânia']
const TEMAS = [
  { valor: 'saude', rotulo: 'Saúde' },
  { valor: 'educacao', rotulo: 'Educação' },
  { valor: 'transporte', rotulo: 'Transporte' },
  { valor: 'cultura', rotulo: 'Cultura', desabilitado: true }
]

const negrito = ref(true)
const alinhamento = ref('centro')
const volume = ref(6)
const faixa = ref([20, 70])
const valor = ref(1250.5)
const codigo = ref('2026')
const assuntos = ref(['Orçamento', 'Saúde'])
const filtros = ref([
  { valor: 'ativos', rotulo: 'Ativos' },
  { valor: 'centro', rotulo: 'Centro' },
  { valor: '2026', rotulo: '2026' }
])
const filtrosMarcados = ref(['ativos'])
const titulo = ref('Sessão ordinária')
const nota = ref(4)
const bairro = ref(undefined)
const cidade = ref('')
const temas = ref(['saude'])

// 8. Functions
function tirarFiltros(valores) {
  filtros.value = filtros.value.filter(item => !valores.includes(item.valor))
}
</script>
