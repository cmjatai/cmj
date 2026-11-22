# Tutorial do frontend v8

Este tutorial é para quem conhece Python e o básico de HTML, CSS e JavaScript, e está começando em
Django e em Vue. Ao fim dele você terá construído uma tela pequena no v8 e saberá onde cada parte
do frontend mora e por quê.

O tutorial ensina. Ele não define regra nenhuma: as regras do v8 estão em `docs/specs/v8/`, e a
referência rápida para quem já conhece o assunto é `docs/frontend/v8.md`.

## O que você vai construir

Uma estante de livros fictícia, em `/v8/estudo/livros/`:

- a lista de livros, desenhada pelo Django, com um filtro por autor;
- uma busca que filtra enquanto você digita e caixas para marcar os livros lidos, feitas em Vue;
- o detalhe de um livro abrindo ao lado, sem sair da página;
- avisos rápidos na tela e um pedido de confirmação;
- um botão que busca a lista de novo no servidor;
- testes para tudo isso.

Os dados são fixos e ficam na memória. Nada é gravado em banco.

## Antes de começar

Você precisa do ambiente de desenvolvimento no ar: o Django respondendo e o servidor de
desenvolvimento do v8 (o Vite) rodando. Os comandos estão no `CLAUDE.md`, na raiz do repositório,
na seção "Comandos". Se for a sua primeira vez, peça a alguém do time para acompanhar a subida do
ambiente: ela depende de um arquivo `.env` que não está no repositório.

Para conferir que está tudo certo, abra `http://localhost:9098/v8/`. Deve aparecer a página inicial
do v8, com o menu no topo. A porta é 9098 quando o Django roda na sua máquina com `runserver`, e
9099 quando roda no container. O tutorial usa 9098.

Você também precisa de um usuário para entrar no sistema, porque a tela do exercício exige login.

## Roteiro

Leia na ordem. Cada capítulo parte do código do anterior.

| Capítulo | O que você aprende |
| --- | --- |
| [01. Visão geral](./01-visao-geral.md) | O que o Django, o Vue e o Vite fazem, e como o v8 junta os três |
| [02. Primeira página](./02-primeira-pagina.md) | Rota, view, serviço e template: uma página inteira só com Django |
| [03. Layouts e blocks](./03-layouts-e-blocks.md) | Herança de templates, os quatro layouts e o que uma página pode preencher |
| [04. Ilhas](./04-ilhas.md) | Um componente Vue dentro da página do Django |
| [05. Drawers, modals e toasts](./05-drawers-modals-toasts.md) | Abrir conteúdo ao lado, pedir confirmação e avisar o usuário |
| [06. HTTP e zona SPA](./06-http-e-zona-spa.md) | Buscar dados no servidor pelo JavaScript, e quando uma tela vira um aplicativo |
| [07. Testes](./07-testes.md) | Testar o lado Django e o lado Vue, e o que fazer antes de um commit |

## Regras do exercício

- Trabalhe num branch seu. O código do exercício **não é para commitar**: ele serve para você
  aprender, e não tem spec.
- Digite o código em vez de colar. É mais lento e você aprende mais.
- Quando algo não funcionar, leia a seção "Se não funcionou" do capítulo antes de pedir ajuda.

Ao terminar, descarte o exercício:

```bash
git restore cmj/v8/views.py cmj/v8/urls.py _frontend/v8/src/core/ilhas.js
rm -r cmj/v8/services/s_estudo.py cmj/v8/tests/test_estudo.py \
      _templates/v8/v8/estudo _templates/v8/v8/partials/estudo \
      _frontend/v8/src/modules/estudo _frontend/v8/tests/estudo
```

## Conferência

O código deste tutorial foi montado e executado em 2026-11-22, sobre o commit `605aa9a6b`: os
testes do capítulo 07 passaram, junto com a suíte do v8. Se algum passo não bater com o que você vê,
o v8 pode ter mudado depois dessa data: confira `docs/frontend/v8.md` e avise o time.
