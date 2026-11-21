# V8: shell

Status: implementado
Última verificação: 2026-11-21 (branch `v8-arquitetura-hibrida`, sobre o commit `32325c9a2`)
Código principal: `cmj/v8/services/s_menu.py`, `cmj/v8/templatetags/v8_tags.py`,
`_templates/v8/v8/shell/`, `_frontend/v8/src/core/shell.js`
Testes: `cmj/v8/tests/test_shell.py`, `_frontend/v8/tests/core/shell.spec.js`,
`_frontend/v8/tests/core/router.spec.js`

O shell é a moldura dos layouts `admin` e `spa`: topbar, sidebar e breadcrumbs. Quem o renderiza é
o Django. O JavaScript só acrescenta o recolher da sidebar, a troca de tema e a gaveta em tela
estreita.

## Escopo

- Serviço: `cmj/v8/services/s_menu.py`.
- Pontos de entrada: a tag `{% v8_menu %}` e os includes `v8/shell/topbar.html`,
  `v8/shell/sidebar.html` e `v8/shell/breadcrumbs.html`.
- Legado tocado: nenhum. O shell só aponta para as rotas existentes de login e logout.

## Regras

### Menu

- V8-SHELL-001 [implementado] O menu é uma árvore declarada em `s_menu.py`. Cada item tem `id`,
  rótulo, URL, ícone, permissão exigida (nenhuma, uma, ou lista em que basta uma) e filhos.
  Evidência: `cmj/v8/services/s_menu.py:17`.
- V8-SHELL-002 [implementado] `menu_para(usuario)` devolve só os itens que o usuário pode ver. Item
  sem permissão exigida aparece para todos, inclusive anônimo. Grupo sem filho visível some.
  Evidência: `cmj/v8/services/s_menu.py:80`.
- V8-SHELL-003 [implementado] A view informa o item ativo pelo `id`. Esse item sai com
  `aria-current="page"`, e os grupos acima dele saem abertos. Evidência:
  `cmj/v8/services/s_menu.py:57`, `_templates/v8/v8/shell/menu.html:9`.
- V8-SHELL-004 [implementado] O menu inicial tem "Início" e o grupo "Demonstração", com os itens de
  `demo.md`. O grupo só aparece para superusuário. Evidência: `cmj/v8/services/s_menu.py:32`.

### Cache do menu

- V8-SHELL-010 [implementado] O HTML do menu fica em `{% cache %}` com chave formada pela versão do
  menu, por um hash do conjunto de permissões do usuário e pelo `id` do item ativo. Usuários com as
  mesmas permissões compartilham a entrada. Evidência: `_templates/v8/v8/shell/sidebar.html:7`.
- V8-SHELL-011 [implementado] Mudança nas permissões de um usuário aparece no menu na requisição
  seguinte, sem invalidação, porque o hash muda. Evidência: `cmj/v8/services/s_global.py:116`.
- V8-SHELL-012 [implementado] O trecho em cache não contém nome, avatar, token CSRF, mensagem nem
  outro dado próprio de um usuário. Evidência: `_templates/v8/v8/shell/sidebar.html:7`,
  `_templates/v8/v8/shell/topbar.html:11`.

### Topbar e breadcrumbs

- V8-SHELL-020 [implementado] A topbar tem a marca, o botão da sidebar, o botão de tema e a área do
  usuário, e não fica em cache. Autenticado vê nome, avatar e "Sair". Anônimo vê "Entrar", com
  retorno para a página atual. Evidência: `_templates/v8/v8/shell/topbar.html:2`.
- V8-SHELL-021 [implementado] As breadcrumbs vêm da lista que a view informa, de pares rótulo e URL.
  O último item não é link e tem `aria-current="page"`. Evidência:
  `_templates/v8/v8/shell/breadcrumbs.html:3`.
- V8-SHELL-022 [implementado] Dentro de uma zona SPA, a rota atual acrescenta seus níveis às
  breadcrumbs do servidor, a partir de `meta.breadcrumb`. Evidência:
  `_frontend/v8/src/core/ZoneOutlet.vue:31`.
- V8-SHELL-023 [implementado] O shell usa `header`, `nav` com rótulo, `main` e um link "Ir para o
  conteúdo" como primeiro elemento focável. Evidência: `_templates/v8/v8/layouts/admin.html:6`.

### Sidebar

- V8-SHELL-030 [implementado] O estado da sidebar fica no cookie `v8_sidebar`, com valor `expandida`
  ou `recolhida`. O Django lê o cookie e renderiza `<html data-sidebar="...">`, de modo que a página
  já chega no estado certo. Sem cookie, vale `expandida`. Evidência:
  `_frontend/v8/src/css/shell.css:182`.
- V8-SHELL-031 [implementado] O botão da sidebar alterna o estado, grava o cookie e atualiza o
  atributo sem recarregar a página. Evidência: `_frontend/v8/src/core/shell.js:67`.
- V8-SHELL-032 [implementado] Em tela estreita a sidebar não ocupa a lateral. O mesmo botão a abre
  como drawer, pelo componente de `overlays.md`, e não altera o cookie. Evidência:
  `_frontend/v8/src/core/boot.js:19`, `_frontend/v8/src/core/shell.js:86`.
- V8-SHELL-033 [implementado] Com o JavaScript desligado, o menu continua visível e seus links
  funcionam, em qualquer largura. Evidência: `_templates/v8/v8/shell/sidebar.html:3`.

### Tema

- V8-SHELL-040 [implementado] O tema fica no cookie `v8_tema`, com valor `claro` ou `escuro`. O
  Django renderiza `<html data-theme="...">` a partir dele. Sem cookie, o atributo não é emitido e o
  CSS segue `prefers-color-scheme`, sem JavaScript. Evidência: `_frontend/v8/src/core/shell.js:27`,
  `_frontend/v8/src/css/tokens.css:78`.
- V8-SHELL-041 [implementado] O botão de tema alterna entre claro e escuro a partir do tema em
  vigor, grava o cookie, atualiza o atributo e o `<meta name="theme-color">`, sem recarregar. O
  botão informa o estado por `aria-pressed`. Evidência: `_frontend/v8/src/core/shell.js:50`.
- V8-SHELL-042 [implementado] Toda cor de template e de componente vem de token semântico com valor
  nos dois temas. Não há cor literal fora de `src/css/tokens.css`. Evidência:
  `_frontend/v8/src/css/tokens.css:3`.

## Requisitos de segurança

- V8-SHELL-050 [implementado] O menu não protege nada: a URL de um item escondido responde 403 ou
  redireciona ao login conforme a view dela. Item da varredura: 1. Evidência: `cmj/v8/views.py:100`.
- V8-SHELL-051 [implementado] Com cache real, dois usuários de permissões diferentes recebem menus
  diferentes, e nenhum recebe item que não pode ver. Item da varredura: 5. Evidência:
  `cmj/v8/services/s_global.py:116`.
- V8-SHELL-052 [implementado] Valor de `v8_sidebar` ou `v8_tema` fora da lista válida é ignorado e
  nunca chega ao HTML. Item da varredura: 6. Evidência: `_frontend/v8/src/core/shell.js:49`.
- V8-SHELL-053 [implementado] O link "Entrar" leva como retorno só o caminho e a query da página
  atual, codificados, sem host. "Sair" usa a rota de logout existente. Item da varredura: 6.
  Evidência: `_templates/v8/v8/shell/topbar.html:21`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-21. O shell não alcança código legado além dos
links de login e logout.

## Dúvidas

Nenhuma.

## Fora do escopo

- Itens de menu para telas reais.
- Preferências guardadas no perfil do usuário, no banco.
- Busca e notificações na topbar.
