# V8: shell

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `6b527f42a`)
Código principal: `cmj/v8/services/s_menu.py`, `cmj/v8/templatetags/v8_tags.py`,
`_templates/v8/v8/layouts/_shell.html`, `_templates/v8/v8/shell/`, `_frontend/v8/src/core/shell.js`,
`_frontend/v8/src/css/temas/oficial/shell.css`
Testes: `cmj/v8/tests/test_shell.py`, `_frontend/v8/tests/core/shell.spec.js`,
`_frontend/v8/tests/core/router.spec.js`, `_frontend/v8/tests/core/fonte.spec.js`,
`cmj/v8/tests/test_arquitetura.py`

O shell é a moldura dos layouts `landing`, `app_topbar` e `app_sidebar` (`templates.md`): cabeçalho,
menu, breadcrumbs e, no `app_sidebar`, a barra lateral. Quem o renderiza é o Django. O JavaScript só
acrescenta o recolher da sidebar, a troca de modo (claro ou escuro), o menu em drawer na tela estreita e o fechar dos
grupos do menu do cabeçalho.

## Escopo

- Serviço: `cmj/v8/services/s_menu.py`.
- Pontos de entrada: a tag `{% v8_menu %}`, os blocks de `v8/layouts/_shell.html` e a parcial
  `v8/shell/menu.html`.
- Legado tocado: nenhum. O shell só aponta para as rotas existentes de login e logout.

## Regras

### Menu

- V8-SHELL-001 [implementado] O menu é uma árvore declarada em `s_menu.py`. Cada item tem `id`,
  rótulo, URL, ícone, permissão exigida (nenhuma, uma, ou lista em que basta uma) e filhos.
  Evidência: `cmj/v8/services/s_menu.py:17`.
- V8-SHELL-002 [implementado] `menu_para(usuario)` devolve só os itens que o usuário pode ver. Item
  sem permissão exigida aparece para todos, inclusive anônimo. Grupo sem filho visível some.
  Evidência: `cmj/v8/services/s_menu.py:114`.
- V8-SHELL-003 [implementado] A view informa o item ativo pelo `id`. Esse item sai com
  `aria-current="page"`, e os grupos acima dele saem abertos. Evidência:
  `cmj/v8/services/s_menu.py:91`, `_templates/v8/v8/shell/menu_itens.html:9`.
- V8-SHELL-004 [implementado] O menu inicial tem "Início", o grupo "Demonstração", com os itens de
  `demo.md`, só para superusuário, e o grupo "Design system", com os de `ds.md`, para todos. Evidência: `cmj/v8/services/s_menu.py:32`.

### Cache do menu

- V8-SHELL-010 [implementado] O HTML do menu fica em `{% cache %}` com chave formada pela versão do
  menu, por um hash do conjunto de permissões do usuário e pelo `id` do item ativo. Usuários com as
  mesmas permissões compartilham a entrada. Evidência: `_templates/v8/v8/shell/menu.html:5`.
- V8-SHELL-011 [implementado] Mudança nas permissões de um usuário aparece no menu na requisição
  seguinte, sem invalidação, porque o hash muda. Evidência: `cmj/v8/services/s_global.py:205`.
- V8-SHELL-012 [implementado] O trecho em cache não contém nome, avatar, token CSRF, mensagem nem
  outro dado próprio de um usuário. Evidência: `_templates/v8/v8/shell/menu.html:5`,
  `_templates/v8/v8/layouts/_shell.html:21`.

### Topbar e breadcrumbs

- V8-SHELL-020 [implementado] A topbar tem a marca, o botão de modo e a área do usuário, e não fica
  em cache. No layout `app_sidebar` tem também o botão da sidebar, e em `app_topbar` e `landing`, o
  botão do menu. Autenticado vê nome, avatar e "Sair". Anônimo vê "Entrar", com retorno para a
  página atual. Evidência: `_templates/v8/v8/layouts/_shell.html:9`,
  `_templates/v8/v8/layouts/app_sidebar.html:8`.
- V8-SHELL-021 [implementado] As breadcrumbs vêm da lista que a view informa, de pares rótulo e URL.
  O último item não é link e tem `aria-current="page"`. O layout `landing` não mostra breadcrumbs.
  Evidência: `_templates/v8/v8/layouts/_shell.html:44`.
- V8-SHELL-022 [implementado] Dentro de uma zona SPA, a rota atual acrescenta seus níveis às
  breadcrumbs do servidor, a partir de `meta.breadcrumb`. Evidência:
  `_frontend/v8/src/core/ZoneOutlet.vue:31`.
- V8-SHELL-023 [implementado] Os três layouts com shell usam `header`, `nav` com rótulo, `main` e um
  link "Ir para o conteúdo" como primeiro elemento focável. Evidência:
  `_templates/v8/v8/layouts/_shell.html:6`.

### Sidebar

- V8-SHELL-030 [implementado] O estado da sidebar fica no cookie `v8_sidebar`, com valor `expandida`
  ou `recolhida`. Nas páginas do layout `app_sidebar`, o Django lê o cookie e renderiza
  `<html data-sidebar="...">`, de modo que a página já chega no estado certo. Sem cookie, vale
  `expandida`. Os outros layouts não emitem o atributo. Evidência:
  `_templates/v8/v8/layouts/app_sidebar.html:4`, `_frontend/v8/src/css/temas/oficial/shell.css:187`.
- V8-SHELL-031 [implementado] O botão da sidebar alterna o estado, grava o cookie e atualiza o
  atributo sem recarregar a página. Evidência: `_frontend/v8/src/core/shell.js:69`.
- V8-SHELL-032 [implementado] Em tela estreita a sidebar não ocupa a lateral. O mesmo botão a abre
  como drawer, pelo componente de `overlays.md`, e não altera o cookie. Evidência:
  `_frontend/v8/src/core/boot.js:20`, `_frontend/v8/src/core/shell.js:88`.
- V8-SHELL-033 [implementado] Com o JavaScript desligado, o menu continua visível e seus links
  funcionam, em qualquer largura, na sidebar e no cabeçalho. Quem garante é o CSS, com
  `@media (scripting: none)`. Evidência: `_frontend/v8/src/css/temas/oficial/shell.css:296`.

### Menu no cabeçalho

- V8-SHELL-034 [implementado] Em `app_topbar` e `landing` o menu fica no cabeçalho, na horizontal,
  com os filhos de cada grupo num painel suspenso. Em tela estreita ele sai do cabeçalho, e o botão
  `data-v8-acao="menu"`, que só aparece nessa largura, o abre como drawer, sem gravar cookie.
  Evidência: `_frontend/v8/src/core/shell.js:130`, `_frontend/v8/src/css/temas/oficial/shell.css:227`.
- V8-SHELL-035 [implementado] No menu do cabeçalho, em tela larga, o grupo do item ativo começa
  fechado, embora o servidor o entregue aberto, para a sidebar. Um grupo aberto fecha ao clicar fora
  dele, ao abrir outro grupo ou com ESC, que devolve o foco ao rótulo do grupo. Os grupos da sidebar
  não são afetados. Evidência: `_frontend/v8/src/core/shell.js:95`,
  `_frontend/v8/src/core/shell.js:105`, `_frontend/v8/src/css/temas/oficial/shell.css:282`.

### Modo claro e escuro

- V8-SHELL-040 [implementado] O modo fica no cookie `v8_modo`, com valor `claro` ou `escuro`. O
  Django renderiza `<html data-modo="...">` a partir dele. Sem cookie, o atributo não é emitido e o
  CSS segue `prefers-color-scheme`, sem JavaScript. Evidência: `_frontend/v8/src/core/shell.js:29`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:93`.
- V8-SHELL-041 [implementado] O botão de modo alterna entre claro e escuro a partir do modo em
  vigor, grava o cookie, atualiza o atributo e o `<meta name="theme-color">`, sem recarregar. O
  botão informa o estado por `aria-pressed`. Evidência: `_frontend/v8/src/core/shell.js:52`.
- V8-SHELL-042 [retirada] Toda cor vinha de token com valor nos dois modos, e cor literal só existia
  em `src/css/tokens.css`. Substituída por V8-TEMA-012 e V8-TEMA-013.

## Requisitos de segurança

- V8-SHELL-050 [implementado] O menu não protege nada: a URL de um item escondido responde 403 ou
  redireciona ao login conforme a view dela. Item da varredura: 1. Evidência: `cmj/v8/views.py:105`.
- V8-SHELL-051 [implementado] Com cache real, dois usuários de permissões diferentes recebem menus
  diferentes, e nenhum recebe item que não pode ver. Item da varredura: 5. Evidência:
  `cmj/v8/services/s_global.py:205`.
- V8-SHELL-052 [implementado] Valor de `v8_sidebar` ou `v8_modo` fora da lista válida é ignorado e
  nunca chega ao HTML. Item da varredura: 6. Evidência: `_frontend/v8/src/core/shell.js:51`.
- V8-SHELL-053 [implementado] O link "Entrar" leva como retorno só o caminho e a query da página
  atual, codificados, sem host. "Sair" usa a rota de logout existente. Item da varredura: 6.
  Evidência: `_templates/v8/v8/layouts/_shell.html:32`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-21. O shell não alcança código legado além dos
links de login e logout.

## Dúvidas

Nenhuma.

## Fora do escopo

- Itens de menu para telas reais.
- Preferências guardadas no perfil do usuário, no banco.
- Busca e notificações na topbar.
