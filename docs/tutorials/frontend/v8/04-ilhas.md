# 04. Ilhas

A página do capítulo 02 filtra por autor, e cada filtro é uma ida ao servidor. Agora você vai
acrescentar duas coisas que acontecem na hora, sem recarregar: uma busca pelo título e caixas para
marcar os livros lidos. Para isso entra o Vue, numa **ilha**.

## A ideia

Uma ilha é um trecho da página do Django que um componente Vue assume. Funciona assim:

1. O Django desenha a página inteira, inclusive o trecho da ilha, como HTML comum.
2. Ele marca esse trecho com o nome da ilha e deixa ao lado, em formato JSON, os dados que o
   componente vai precisar.
3. Quando o JavaScript carrega, o aplicativo Vue da página acha a marca, busca o componente com
   aquele nome e o coloca no lugar do HTML que estava ali.

O HTML que o Django desenhou dentro da ilha tem dois papéis: é o que o usuário vê enquanto o
JavaScript não chega, e é o que ele continua vendo se o JavaScript falhar. Por isso a ilha não
nasce vazia.

## 1. A view entrega os dados da ilha

Em `cmj/v8/views.py`, troque a última linha do contexto de `EstudoLivrosView`:

```python
            {"autor": autor, "livros": livros, "props_livros": {"livros": livros}},
```

`props_livros` é um dicionário. Cada chave dele vira uma **prop** do componente: aqui, uma prop
chamada `livros`.

## 2. O template marca a ilha

Em `livros.html`, acrescente `{% load v8_tags %}` na segunda linha e envolva a tabela com a tag da
ilha:

```django
{% extends "v8/layouts/app_sidebar.html" %}
{% load v8_tags %}
{% block content %}
  <h1 class="v8-pagina-titulo">Livros</h1>

  <form method="get" action="{% url 'cmj.v8:estudo_livros' %}" class="v8-barra-acoes">
    ...o formulário continua igual...
  </form>

  {% v8_island "estudo-livros" props_livros %}
    <table class="v8-tabela">
      ...a tabela continua igual...
    </table>
  {% endv8_island %}
{% endblock %}
```

- `{% load v8_tags %}` torna disponíveis os comandos próprios do v8. Sem ele, o Django não conhece
  `v8_island`.
- `{% v8_island "estudo-livros" props_livros %}` recebe o nome da ilha e os dados.

Recarregue a página e veja o código-fonte (Ctrl+U). Procure por `estudo-livros`. Você vai achar
isto:

```html
<script id="v8-island-1" type="application/json">{"livros": [{"id": 1, ...}]}</script>
<div data-vue-island="estudo-livros" data-props-id="v8-island-1">
  <table class="v8-tabela">...</table>
</div>
```

O `<script type="application/json">` não é código: é só um lugar para guardar dados, que o
navegador não executa. Essa é a **única** forma de passar dado do Django para o JavaScript no v8. O
Django cuida de escapar o conteúdo, de modo que um título de livro malicioso não vira código.

A página continua igual na tela, porque ainda não existe o componente. Abra o Console (F12): há um
aviso "Ilha desconhecida: estudo-livros". É o aplicativo dizendo que achou a marca e não sabe o
que pôr nela.

## 3. O componente

Crie a pasta `_frontend/v8/src/modules/estudo/ilhas/` e, nela, o arquivo `LivrosTabela.vue`:

```vue
<template>
  <div>
    <div class="v8-barra-acoes">
      <label
        class="v8-rotulo"
        for="estudo-busca"
      >Buscar no título</label>
      <input
        id="estudo-busca"
        v-model="busca"
        class="v8-entrada"
        type="search"
      >
    </div>
    <table class="v8-tabela">
      <thead>
        <tr>
          <th scope="col">
            Lido
          </th>
          <th scope="col">
            Título
          </th>
          <th scope="col">
            Autor
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="livro in visiveis"
          :key="livro.id"
        >
          <td>
            <input
              type="checkbox"
              :checked="livro.lido"
              :aria-label="'Lido: ' + livro.titulo"
              @change="alternar(livro)"
            >
          </td>
          <td>{{ livro.titulo }}</td>
          <td>{{ livro.autor }}</td>
        </tr>
        <tr v-if="!visiveis.length">
          <td colspan="3">
            Nenhum livro com esse título.
          </td>
        </tr>
      </tbody>
    </table>
    <p aria-live="polite">
      {{ resumo }}
    </p>
  </div>
</template>
<script setup>
// Ilha `estudo-livros`, do tutorial: a tabela de livros com busca e marcação de lidos.

// 1. Imports
import { computed, ref } from 'vue'

// 2. Composables
// 3. Props & Emits
const props = defineProps({
  // Livros que o Django já desenhou: { id, titulo, autor, lido }.
  livros: {
    type: Array,
    default: () => []
  }
})

// 4. State & Refs
const lista = ref(props.livros.map(livro => ({ ...livro })))
const busca = ref('')

// 5. Computed Properties
const visiveis = computed(() => {
  const termo = busca.value.trim().toLowerCase()
  return lista.value.filter(livro => livro.titulo.toLowerCase().includes(termo))
})
const lidos = computed(() => lista.value.filter(livro => livro.lido).length)
const resumo = computed(() => `${lidos.value} de ${lista.value.length} lidos`)

// 6. Watchers
// 7. Events & Lifecycle Hooks
// 8. Functions
function alternar(livro) {
  livro.lido = !livro.lido
}
</script>
```

### Lendo o `<script setup>`

Todo componente novo do v8 tem estas oito seções, sempre nesta ordem, mesmo as vazias. Assim
qualquer pessoa acha o que procura em qualquer componente.

- **Props** (seção 3). `defineProps` declara o que o componente recebe. A prop `livros` é a chave
  `livros` do dicionário que a view montou.
- **Estado** (seção 4). `ref(valor)` cria um valor que o Vue observa. No JavaScript você lê e
  altera com `.value`: `busca.value`. No `<template>` não precisa do `.value`.
- **Por que copiar as props para `lista`?** Props são de leitura: quem manda nelas é quem as
  entregou. Como o componente vai alterar o campo `lido`, ele trabalha numa cópia.
- **Valores calculados** (seção 5). `visiveis` depende de `busca` e de `lista`. Sempre que um dos
  dois muda, o Vue recalcula `visiveis` e redesenha as linhas. Você nunca manda redesenhar.
- **Funções** (seção 8). `alternar` inverte o campo `lido` de um livro. A contagem em `resumo` se
  atualiza sozinha, porque depende de `lista`.

### Lendo o `<template>`

- `v-model="busca"` liga o campo ao estado: o que a pessoa digita vai para `busca`, e vice-versa.
- `v-for="livro in visiveis"` repete o `<tr>` para cada livro. `:key` dá uma identidade a cada
  linha, para o Vue saber qual é qual quando a lista muda.
- `:checked="livro.lido"`: os dois pontos dizem que o valor é uma expressão JavaScript, e não um
  texto.
- `@change="alternar(livro)"` chama a função quando a caixa muda.
- `v-if` mostra a linha "Nenhum livro" só quando a lista filtrada está vazia.
- `{{ resumo }}` escreve um valor, como no Django. As chaves são iguais por coincidência, e não se
  misturam: o Vue **nunca** interpreta o HTML que o Django escreveu, só os arquivos `.vue`.

## 4. O registro

Falta dizer ao aplicativo qual componente atende pelo nome `estudo-livros`. Abra
`_frontend/v8/src/core/ilhas.js` e acrescente uma linha:

```js
export const ilhas = {
  'demo-clientes-tabela': () => import('~@/modules/demo/ilhas/ClientesTabela.vue'),
  'estudo-livros': () => import('~@/modules/estudo/ilhas/LivrosTabela.vue')
}
```

- `~@/` é um atalho para `_frontend/v8/src/`.
- `() => import(...)` só baixa o arquivo do componente quando uma página realmente tem essa ilha.
- O nome à esquerda tem que ser idêntico ao que está no template do Django.

## Veja funcionando

Recarregue a página. A tabela mudou: a coluna "Lido" veio para a esquerda e virou uma caixa de
marcar, e apareceu o campo "Buscar no título". É a prova de que o componente assumiu o trecho.

- Digite `vidas` no campo. A tabela filtra a cada letra, e o endereço não muda.
- Marque e desmarque os livros. A linha "1 de 3 lidos" acompanha.
- Recarregue a página. As marcações voltam ao que eram: o componente só mudou a cópia que estava
  na memória do navegador. Gravar exigiria um pedido ao servidor, assunto do capítulo 06.

Agora compare as duas visões da página:

- **Ctrl+U** mostra a tabela do Django, com a coluna "Lido" à direita e "Sim" ou "Não".
- **F12, aba Elementos** mostra a tabela do Vue.

Por fim, desligue o JavaScript (F12, Ctrl+Shift+P, digite "JavaScript" e escolha "Desativar
JavaScript") e recarregue. A tabela do Django aparece e o filtro por autor continua funcionando.
Religue depois.

## O filtro por autor e a busca por título

A página ficou com dois filtros, e eles são diferentes de propósito:

| | Filtro por autor | Busca por título |
| --- | --- | --- |
| Quem faz | Django | Vue |
| Onde acontece | No servidor, com um pedido novo | No navegador, sobre o que já chegou |
| Fica no endereço | Sim: dá para copiar o link | Não |
| Sem JavaScript | Funciona | Não existe |

Nenhum dos dois é o "certo". Filtro que precisa de link, ou que percorre muitos dados, fica no
servidor. Conforto sobre os dados que já estão na tela pode ficar no navegador.

## Se não funcionou

- **"Ilha desconhecida" no Console**: o nome no template e o nome em `ilhas.js` estão diferentes.
- **A tabela não muda e o Console não mostra nada**: o JavaScript não chegou. Confira se o servidor
  do Vite está no ar e, na aba Rede, se os pedidos à porta 5174 respondem.
- **Erro vermelho numa faixa por cima da página**: é o Vite avisando de um erro no arquivo `.vue`.
  Leia a mensagem, que traz a linha.
- **`Invalid block tag: 'v8_island'`**: faltou `{% load v8_tags %}` no template.
- **A tabela aparece vazia**: `props_livros` precisa ser um dicionário com a chave `livros`.

## Para praticar

1. Mostre o autor em negrito quando o livro estiver lido. Dica: `:class="{ 'font-semibold': livro.lido }"`.
2. Acrescente ao resumo quantos livros a busca está mostrando.
3. Abra `_frontend/v8/src/modules/demo/ilhas/ClientesTabela.vue`, a ilha da demonstração, e
   identifique as oito seções e o que cada valor calculado faz.

Próximo: [05. Drawers, modals e toasts](./05-drawers-modals-toasts.md).
