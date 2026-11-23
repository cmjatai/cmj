<template>
  <div class="grid gap-8 lg:grid-cols-2">
    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">BarraMenus, BarraFerramentas</code>
      <BarraMenus
        :menus="MENUS"
        @selecionar="valor => (acao = valor)"
      />
      <BarraFerramentas
        v-model="estilo"
        rotulo="Formatação"
        multiplo
        :itens="FERRAMENTAS"
        :alternadores="ESTILOS"
        @acionar="valor => (acao = valor)"
      />
      <p
        class="text-sm text-texto-suave"
        data-ds-acao-escolhida
      >
        {{ acao }}
      </p>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">MenuNavegacao, CartaoFlutuante</code>
      <MenuNavegacao
        rotulo="Navegação de exemplo"
        :itens="NAVEGACAO"
      />
      <CartaoFlutuante>
        <template #gatilho>
          <a href="#ds-estrutura">Vereadora Exemplo</a>
        </template>
        <div class="flex items-center gap-3">
          <Avatar
            nome="Vereadora Exemplo"
            tamanho="lg"
          />
          <div>
            <p class="font-semibold">
              Vereadora Exemplo
            </p>
            <p class="text-sm text-texto-suave">
              Partido Exemplo
            </p>
          </div>
        </div>
      </CartaoFlutuante>
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">MenuContexto, Recolhivel</code>
      <MenuContexto
        :itens="CONTEXTO"
        @selecionar="valor => (acao = valor)"
      >
        <div class="v8-cartao">
          Clique com o botão direito aqui.
        </div>
      </MenuContexto>
      <Recolhivel
        v-model:open="recolhivelAberto"
        titulo="Mais detalhes"
      >
        <p>Conteúdo que abre e fecha.</p>
      </Recolhivel>
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">Paginacao, Etapas</code>
      <Paginacao
        v-model:page="pagina"
        :total="240"
        :por-pagina="20"
      />
      <Etapas
        v-model="etapa"
        :passos="ETAPAS"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Arvore</code>
      <Arvore
        v-model="pasta"
        v-model:expanded="pastasAbertas"
        rotulo="Pastas"
        :itens="PASTAS"
      />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Divisor, AreaRolagem</code>
      <Divisor :tamanhos="[35, 65]">
        <template #primeiro>
          <p>Painel um</p>
        </template>
        <template #segundo>
          <AreaRolagem
            class="h-32"
            rotulo="Itens"
          >
            <ul class="p-2">
              <li
                v-for="numero in 30"
                :key="numero"
              >
                Item {{ numero }}
              </li>
            </ul>
          </AreaRolagem>
        </template>
      </Divisor>
    </div>

    <div class="flex flex-col gap-3">
      <code class="text-xs text-texto-suave">Avatar, Separador, Progresso</code>
      <div class="flex items-center">
        <Avatar
          nome="Ana Lima"
          tamanho="sm"
        />
        <Separador
          orientacao="vertical"
          decorativo
        />
        <Avatar nome="Bruno Costa" />
        <Separador
          orientacao="vertical"
          decorativo
        />
        <Avatar
          nome="Carla"
          tamanho="lg"
        />
      </div>
      <Separador />
      <Progresso
        v-model="progresso"
        rotulo="Envio"
      />
      <Progresso rotulo="Carregando" />
    </div>

    <div class="flex flex-col gap-2">
      <code class="text-xs text-texto-suave">Proporcao</code>
      <Proporcao :proporcao="16 / 9">
        <div class="grid h-full place-items-center text-texto-suave">
          16:9
        </div>
      </Proporcao>
    </div>
  </div>
</template>

<script setup>
// Ilha `ds-estrutura` da vitrine (V8-DS-016): os componentes de navegação e estrutura de
// componentes.md, com dados de amostra. Nada é enviado ao servidor (V8-DS-044).

// 1. Imports
import { ref } from 'vue'
import AreaRolagem from '~@/componentes/AreaRolagem.vue'
import Arvore from '~@/componentes/Arvore.vue'
import Avatar from '~@/componentes/Avatar.vue'
import BarraFerramentas from '~@/componentes/BarraFerramentas.vue'
import BarraMenus from '~@/componentes/BarraMenus.vue'
import CartaoFlutuante from '~@/componentes/CartaoFlutuante.vue'
import Divisor from '~@/componentes/Divisor.vue'
import Etapas from '~@/componentes/Etapas.vue'
import MenuContexto from '~@/componentes/MenuContexto.vue'
import MenuNavegacao from '~@/componentes/MenuNavegacao.vue'
import Paginacao from '~@/componentes/Paginacao.vue'
import Progresso from '~@/componentes/Progresso.vue'
import Proporcao from '~@/componentes/Proporcao.vue'
import Recolhivel from '~@/componentes/Recolhivel.vue'
import Separador from '~@/componentes/Separador.vue'

// 4. State & Refs
const MENUS = [
  {
    valor: 'arquivo',
    rotulo: 'Arquivo',
    itens: [
      { valor: 'novo', rotulo: 'Novo' },
      { valor: 'abrir', rotulo: 'Abrir' },
      { separador: true },
      { valor: 'sair', rotulo: 'Sair', perigo: true }
    ]
  },
  {
    valor: 'editar',
    rotulo: 'Editar',
    itens: [
      { valor: 'desfazer', rotulo: 'Desfazer' },
      { valor: 'refazer', rotulo: 'Refazer', desabilitado: true }
    ]
  }
]
const FERRAMENTAS = [
  { valor: 'salvar', rotulo: 'Salvar' },
  { valor: 'imprimir', rotulo: 'Imprimir' },
  { separador: true },
  { rotulo: 'Ajuda', href: '#ds-estrutura' }
]
const ESTILOS = [
  { valor: 'negrito', rotulo: 'N', rotuloAcessivel: 'Negrito' },
  { valor: 'italico', rotulo: 'I', rotuloAcessivel: 'Itálico' }
]
const NAVEGACAO = [
  { valor: 'vitrine', rotulo: 'Vitrine', href: '#ds-cores', ativo: true },
  {
    valor: 'temas',
    rotulo: 'Temas',
    links: [
      { rotulo: 'Lista de temas', href: '/v8/ds/temas/', descricao: 'Prévia e escolha do tema' },
      { rotulo: 'Cores', href: '#ds-cores', descricao: 'Os tokens de cor do tema em vigor' }
    ]
  }
]
const CONTEXTO = [
  { valor: 'copiar', rotulo: 'Copiar' },
  { valor: 'colar', rotulo: 'Colar' },
  { separador: true },
  { valor: 'excluir', rotulo: 'Excluir', perigo: true }
]
const ETAPAS = [
  { titulo: 'Protocolo', descricao: 'Recebida' },
  { titulo: 'Comissão', descricao: 'Em análise' },
  { titulo: 'Plenário', descricao: 'Votação' }
]
const PASTAS = [
  {
    valor: 'documentos',
    rotulo: 'Documentos',
    filhos: [
      { valor: 'atas', rotulo: 'Atas' },
      { valor: 'pautas', rotulo: 'Pautas', filhos: [{ valor: 'pauta-42', rotulo: 'Pauta 42' }] }
    ]
  },
  { valor: 'imagens', rotulo: 'Imagens' }
]

const acao = ref('')
const estilo = ref(['negrito'])
const recolhivelAberto = ref(false)
const pagina = ref(3)
const etapa = ref(2)
const pasta = ref(undefined)
const pastasAbertas = ref(['documentos'])
const progresso = ref(60)
</script>
