# 03. Layouts e blocks

No capítulo anterior a sua página ganhou cabeçalho, menu e trilha sem você escrever nenhum deles.
Este capítulo explica de onde eles vieram e o que você pode trocar.

## Herança de templates

Pense num formulário de papel já impresso, com campos em branco. Quem imprime decide a estrutura.
Quem preenche só escreve nos campos. No Django:

- o template "impresso" marca cada campo com `{% block nome %}...{% endblock %}`;
- o template que "preenche" começa com `{% extends "..." %}` e escreve blocks com os mesmos nomes.

O que o filho não preenche fica como o pai deixou. Essa é a herança de templates, e ela pode ter
mais de um nível: um template estende outro, que estende outro.

## Os três níveis do v8

```text
base_v8.html                     nível 1: o esqueleto do documento
├─ v8/layouts/minimal.html       nível 2: os layouts
└─ v8/layouts/_shell.html
   ├─ v8/layouts/landing.html
   ├─ v8/layouts/app_topbar.html
   └─ v8/layouts/app_sidebar.html
      └─ v8/estudo/livros.html   nível 3: a sua página
```

- **Nível 1, a base.** Tem só o que todo documento HTML precisa: `<html>`, `<head>`, `<body>`, a
  referência ao JavaScript e os dados que o JavaScript lê. Não tem nada visível.
- **Nível 2, os layouts.** Definem a moldura. Três deles compartilham a mesma estrutura, escrita uma
  vez em `_shell.html`: cabeçalho, área lateral, trilha, conteúdo, rodapé. Cada layout só troca o
  que é diferente nele.
- **Nível 3, as páginas.** Escolhem um layout e preenchem o conteúdo.

Abra `_templates/v8/v8/layouts/_shell.html` e leia. Você vai reconhecer o cabeçalho, o botão de
tema, a área do usuário e, lá no meio, `{% block content %}{% endblock %}`: é a lacuna que a sua
página preencheu. Depois abra `app_sidebar.html`: ele é curto, porque só acrescenta a barra lateral.

`_shell.html` começa com `_` porque é **abstrato**: existe para os layouts estenderem. Uma página
nunca o estende direto.

## Os quatro layouts

| Layout | Para quê | Como é |
| --- | --- | --- |
| `app_sidebar` | Telas de trabalho | Menu numa barra à esquerda, conteúdo ocupando o resto |
| `app_topbar` | Funcionalidades com menu no topo | Menu na horizontal, conteúdo centralizado |
| `landing` | Capa e páginas institucionais | Menu no topo, faixa de destaque, rodapé |
| `minimal` | Login, erro, telas de foco | Só o conteúdo, no centro da tela |

### Experimento 1: trocar de layout

Na primeira linha de `livros.html`, troque `app_sidebar` por `app_topbar`, salve e recarregue a
página. O menu foi para o topo e o conteúdo ficou centralizado. Você mudou uma palavra.

Repita com `landing` e com `minimal`. Repare:

- em `landing` a trilha some e aparece um rodapé;
- em `minimal` somem o cabeçalho e o menu.

A sua página funcionou nos quatro porque todos oferecem o block `content`. Volte para
`app_sidebar` antes de continuar.

Você pode ver os quatro lado a lado em `/v8/demo/layouts/landing/` e nas páginas vizinhas. Elas
exigem superusuário.

## Os blocks que uma página pode preencher

`content` é o principal, e há outros. Os mais usados:

| Block | O que é |
| --- | --- |
| `content` | O conteúdo da página |
| `breadcrumbs` | A trilha de navegação |
| `hero` | Uma faixa de largura total, antes do conteúdo |
| `meta` | Marcações de `<head>` para buscadores, como a descrição da página |
| `page_data` | Dados da página para o JavaScript |
| `assets` e `scripts` | Arquivos extras do Vite, no `<head>` e no fim do `<body>` |

A tabela completa está na seção "Templates em camadas" de `docs/frontend/v8.md`.

### Experimento 2: preencher outro block

Acrescente no fim de `livros.html`, depois do `{% endblock %}` do conteúdo:

```django
{% block meta %}
  <meta name="description" content="Estante de exemplo do tutorial do v8.">
{% endblock %}
```

Recarregue e veja o código-fonte com Ctrl+U. A linha apareceu dentro do `<head>`, embora você a
tenha escrito no fim do arquivo. A posição no HTML final é a do block no template pai, não a do
seu arquivo.

### Experimento 3: acrescentar em vez de trocar

Preencher um block **substitui** o que o pai tinha. Para manter o conteúdo do pai e acrescentar o
seu, use `{{ block.super }}`:

```django
{% block breadcrumbs %}
  {{ block.super }}
  <p class="v8-aviso-demo">Tela de exercício do tutorial.</p>
{% endblock %}
```

Recarregue: a trilha continua lá, com o aviso logo abaixo. Agora apague a linha `{{ block.super }}`
e recarregue de novo: a trilha sumiu, porque o seu block tomou o lugar do original. Devolva a
linha.

## De onde vem o título da aba

Você não escreveu `<title>`, e a aba do navegador mostra "Livros · PortalCMJ". O título vem do
primeiro argumento de `dados_layout(...)`, na view. A base o usa para montar o `<title>`.

Essa é a única informação que os layouts leem da view: uma variável chamada `v8`, com o título, a
trilha e o item de menu ativo. Tudo o mais que a view entrega é da sua página.

## O que uma página não faz

- **Não estende `base_v8.html` nem `_shell.html`.** Sempre um dos quatro layouts.
- **Não preenche os blocks `layout`, `html_attrs` nem `layout_name`.** Eles pertencem aos layouts:
  são eles que montam a estrutura.
- **Não cria arquivo na raiz de `_templates/v8/`.** Essa pasta é consultada antes das pastas do
  resto do portal, e um arquivo ali, como `base.html`, tomaria o lugar do arquivo de mesmo nome do
  portal inteiro. Tudo o que é do v8 vai dentro de `_templates/v8/v8/`.
- **Não escreve `<script>` no template.** Dados para o JavaScript vão por um mecanismo próprio, que
  você usa no próximo capítulo.

Há testes automáticos que conferem cada uma dessas regras.

## Quando usar `{% include %}`

`{% include "arquivo.html" %}` cola outro template naquele ponto. É útil para um trecho repetido em
várias páginas. No v8 a preferência é por blocks, e quando um include é necessário ele fica
**dentro de um block**, para que quem estende o template possa trocá-lo. Um exemplo está em
`_shell.html`: o menu entra por include, dentro de um block.

## Para praticar

1. Estenda `landing` e preencha o block `hero`:

   ```django
   {% block hero %}
     <section class="v8-hero">
       <div class="v8-hero-miolo">
         <h1 class="v8-pagina-titulo">Estante</h1>
         <p>Os livros do tutorial.</p>
       </div>
     </section>
   {% endblock %}
   ```

   Veja onde a faixa aparece. Depois volte para `app_sidebar` e apague o block.
2. Abra `_templates/v8/v8/erros/404.html` e descubra qual layout a página de erro usa, e por quê.
3. Desfaça os experimentos 2 e 3. O arquivo deve voltar a ter só o `extends` e o block `content`.

Próximo: [04. Ilhas](./04-ilhas.md).
