# 05. Drawers, modals e toasts

Três formas de mostrar algo por cima da página, sem sair dela:

- **Drawer**: um painel que desliza de um lado. Serve para um detalhe, um filtro, uma ajuda.
- **Modal**: uma janela no centro. Serve para uma decisão ou um formulário curto.
- **Toast**: um aviso curto num canto, que some sozinho. Serve para dizer que algo deu certo ou
  errado.

O v8 já tem os três prontos. Você não cria o painel nem a janela: você pede que eles abram. Todos
fecham com ESC, devolvem o foco ao lugar de onde vieram e funcionam nos dois temas.

Neste capítulo o título de cada livro vai abrir o detalhe num drawer, marcar um livro vai mostrar
um toast, e um botão novo vai pedir confirmação num modal.

## Parte A: um drawer aberto por um link

O detalhe do livro vai ser desenhado pelo Django, como um **fragmento**: um pedaço de HTML sem a
página em volta. O drawer busca esse pedaço e o mostra.

### 1. O template do fragmento

Crie a pasta `_templates/v8/v8/partials/estudo/` e, nela, o arquivo `livro.html`:

```django
<section>
  <h2 data-overlay-title>{{ livro.titulo }}</h2>
  <dl class="v8-lista-dados">
    <dt>Autor</dt>
    <dd>{{ livro.autor }}</dd>
    <dt>Lido</dt>
    <dd>{% if livro.lido %}Sim{% else %}Não{% endif %}</dd>
  </dl>
</section>
```

Não há `extends` nem block: um fragmento é só o trecho. O texto do elemento com
`data-overlay-title` vira o título do drawer. Templates de fragmento ficam sempre em
`v8/partials/`.

### 2. A view do fragmento

Em `cmj/v8/views.py`, depois de `EstudoLivrosView`:

```python
class EstudoLivroFragmento(FragmentoV8View):
    exige = s_global.AUTENTICADO
    template_name = "v8/partials/estudo/livro.html"

    def get(self, request, pk):
        livro = s_estudo.obter(int(pk))
        if livro is None:
            raise Http404
        return self.responder_fragmento({"livro": livro})
```

- `FragmentoV8View` é a classe base dos fragmentos.
- `exige` aparece de novo. O fragmento tem endereço próprio, e qualquer pessoa pode digitá-lo no
  navegador. Por isso ele confere o acesso por conta própria, sem contar com a página que o abre.
- `pk` vem do endereço. `raise Http404` responde "não encontrado" quando o livro não existe.

### 3. A rota do fragmento

Em `cmj/v8/urls.py`, depois da rota da página:

```python
    re_path(
        r"^v8/_frag/estudo/livro/(?P<pk>\d+)/$",
        views.EstudoLivroFragmento.as_view(),
        name="estudo_frag_livro",
    ),
```

- Todo fragmento mora sob `/v8/_frag/`.
- `(?P<pk>\d+)` captura um número do endereço e o entrega à view com o nome `pk`.

Teste agora, antes de ligar ao drawer: abra `http://localhost:9098/v8/_frag/estudo/livro/2/`. Deve
aparecer o detalhe de "Vidas Secas", sem moldura e sem estilo. É isso mesmo: é só o pedaço.

### 4. O link que abre o drawer

Em `livros.html`, troque a célula do título:

```django
<td><a href="{% url 'cmj.v8:estudo_frag_livro' livro.id %}" data-drawer="frag:estudo/livro/{{ livro.id }}" data-drawer-side="right">{{ livro.titulo }}</a></td>
```

E em `LivrosTabela.vue`, troque `<td>{{ livro.titulo }}</td>` por:

```vue
          <td>
            <a
              :href="'/v8/_frag/estudo/livro/' + livro.id + '/'"
              :data-drawer="'frag:estudo/livro/' + livro.id"
              data-drawer-side="right"
            >{{ livro.titulo }}</a>
          </td>
```

Você escreveu o link duas vezes porque a tabela existe duas vezes: a do Django, que aparece antes
do JavaScript, e a do Vue, que a substitui.

O que cada atributo faz:

- `data-drawer="frag:estudo/livro/2"` pede um drawer com o fragmento de `/v8/_frag/estudo/livro/2/`.
  O texto depois de `frag:` é o caminho, sem a barra do começo nem a do fim.
- `data-drawer-side="right"` escolhe o lado.
- `href` é o caminho normal do link. Se o JavaScript não estiver disponível, o clique segue para
  ele. Aqui ele aponta para o próprio fragmento, para o exercício ficar curto. Numa tela de verdade
  ele aponta para uma página completa com o mesmo conteúdo.

Você não escreveu nenhum JavaScript para abrir o drawer. O v8 tem um único ouvinte de cliques na
página inteira, que reconhece o atributo `data-drawer` em qualquer link, inclusive nos que o Vue
desenha.

### Veja funcionando

Recarregue e clique no título de um livro. O detalhe desliza da direita, com o título do livro no
alto. Experimente fechar de três jeitos: ESC, o botão de fechar e um clique fora do painel.

Abra a aba Rede (F12) e clique em outro livro. Aparece um pedido a `/v8/_frag/estudo/livro/…/`: o
navegador buscou só o pedaço.

## Parte B: um toast

Toast se pede pelo JavaScript. Em `LivrosTabela.vue`:

Na seção de imports, acrescente:

```js
import { useToast } from '~@/overlays/useToast'
```

Na seção de composables:

```js
// 2. Composables
const toast = useToast()
```

E troque a função `alternar`:

```js
function alternar(livro) {
  livro.lido = !livro.lido
  toast.success(livro.lido ? `"${livro.titulo}" marcado como lido.` : `"${livro.titulo}" desmarcado.`)
}
```

Marque um livro: o aviso aparece e some depois de alguns segundos. Além de `success` existem
`info`, `warning` e `error`. O de erro não some sozinho, porque a pessoa precisa lê-lo.

Uma função cujo nome começa com `use`, como `useToast`, é um **composable**: uma função que
entrega ao componente algo pronto para usar. Elas ficam na seção 2.

O Django também gera toasts. Quando uma view chama `messages.success(request, "...")`, a mensagem
aparece como toast na página seguinte.

## Parte C: um modal de confirmação

Vamos acrescentar um botão "Desmarcar todos", que pergunta antes de agir.

Na seção de imports:

```js
import { useModal } from '~@/overlays/useModal'
```

Na seção de composables:

```js
const { confirm } = useModal()
```

Na seção de funções:

```js
async function desmarcarTodos() {
  const confirmou = await confirm({
    titulo: 'Desmarcar todos',
    mensagem: 'Desmarcar todos os livros lidos?',
    rotuloOk: 'Desmarcar'
  })
  if (!confirmou) {
    return
  }
  lista.value.forEach(livro => {
    livro.lido = false
  })
}
```

E no `<template>`, dentro da `<div class="v8-barra-acoes">`, depois do campo de busca:

```vue
      <button
        type="button"
        class="v8-btn v8-btn-fantasma"
        :disabled="!lidos"
        @click="desmarcarTodos"
      >
        Desmarcar todos
      </button>
```

O ponto novo é o `await`. `confirm(...)` abre o modal e devolve uma **Promise**: um valor que só
fica pronto depois, quando a pessoa responder. `await` espera por ele. O resultado é `true` se ela
confirmou e `false` se cancelou, apertou ESC ou clicou fora. Para usar `await`, a função precisa
ser declarada com `async`.

`:disabled="!lidos"` desliga o botão quando não há livro marcado. `lidos` é o valor calculado do
capítulo anterior.

Teste: marque dois livros, clique em "Desmarcar todos" e cancele. Nada muda. Clique de novo e
confirme.

## Um aviso sobre confirmação

O modal de confirmação protege contra um clique por engano. Ele **não protege contra ninguém**:
quem quiser pode chamar o servidor direto. Toda ação que grava ou apaga precisa ser conferida no
servidor, pela view.

## O que mais existe

Você usou uma parte pequena. A lista completa, com exemplos, está nas seções "Gatilhos em HTML",
"Drawers", "Modals" e "Toasts" de `docs/frontend/v8.md`. Para ter ideia:

- `data-drawer="el:#filtros"` abre num drawer um elemento que já está na página.
- `data-confirm="Mensagem"` num formulário ou link pede confirmação antes de seguir, sem JavaScript
  seu.
- `openForm` abre um formulário num modal e mostra os erros de validação do Django junto a cada
  campo.
- Um drawer pode ficar registrado no endereço, de modo que o botão voltar do navegador o feche e o
  link copiado o reabra.

A demonstração em `/v8/demo/clientes/` usa todos eles. Ela exige superusuário.

## Se não funcionou

- **O clique abre o fragmento como página, em vez do drawer**: o JavaScript não está atendendo, ou
  o texto de `data-drawer` tem um caractere fora do padrão. O caminho só aceita letras, números,
  `-`, `_` e `/`.
- **O drawer abre com uma mensagem de erro no lugar do detalhe**: confira a rota do fragmento. Teste
  o endereço dele direto no navegador.
- **`ValueError: Fragmento fora de v8/partials/`**: o template do fragmento precisa estar na pasta
  `v8/partials/`.
- **`toast is not defined`**: faltou a linha `const toast = useToast()`.

## Para praticar

1. Troque o lado do drawer para `left` e o tamanho com `data-drawer-size="sm"`.
2. Mostre um `toast.info` depois de desmarcar todos, dizendo quantos livros foram desmarcados.
   Atenção à ordem: conte antes de desmarcar.
3. Abra direto no navegador o fragmento de um livro que não existe,
   `/v8/_frag/estudo/livro/99/`, e veja na aba Rede o status da resposta.

Próximo: [06. HTTP e zona SPA](./06-http-e-zona-spa.md).
