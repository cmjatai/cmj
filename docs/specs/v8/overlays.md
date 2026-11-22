# V8: overlays

Status: implementado
Última verificação: 2026-11-21 (branch `v8-arquitetura-hibrida`, sobre o commit `32325c9a2`)
Código principal: `_frontend/v8/src/overlays/`, `_frontend/v8/src/core/triggers.js`,
`cmj/v8/views.py` (fragmentos), `_templates/v8/v8/partials/`
Testes: `_frontend/v8/tests/overlays/`, `_frontend/v8/tests/core/router.spec.js`,
`cmj/v8/tests/test_fragmentos.py`, `_frontend/v8/tests/core/fonte.spec.js`

Drawers, modals e toasts têm uma implementação só, usada igualmente por páginas Django com ilhas e
por zonas SPA. Os primitivos de foco e acessibilidade vêm do Reka UI. A pilha, as Promises e a
ligação com a URL ficam no `OverlayStore`.

## Escopo

- Frontend: `OverlayStore`, `OverlayHost.vue`, `Drawer.vue`, os modals padrão, `ToastHost.vue`, os
  composables `useDrawer`, `useModal`, `useToast` e `useOverlay`, e a delegação de cliques.
- Django: a view base de fragmento e as rotas `^v8/_frag/`.
- Legado tocado: nenhum.

## Regras

### Camadas

- V8-OVL-001 [implementado] As camadas são tokens CSS, nesta ordem crescente: `--z-base`,
  `--z-sticky`, `--z-drawer`, `--z-modal`, `--z-toast` e `--z-popover` (popover e tooltip).
  Evidência: `_frontend/v8/src/css/tokens.css:30`.
- V8-OVL-002 [implementado] Nenhum `z-index` em `_frontend/v8/src` ou `_templates/v8` tem valor
  literal: todos usam um token. Evidência: `_frontend/v8/src/css/overlays.css:1`.
- V8-OVL-003 [implementado] Um overlay aberto por cima de outro nunca fica atrás dele, mesmo sendo
  de camada menor, como um drawer aberto a partir de um modal. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:227`, `_frontend/v8/src/overlays/OverlayStore.js:50`.

### Pilha

- V8-OVL-010 [implementado] Drawers em modo `overlay` e modals entram, por ordem de abertura, numa
  única pilha no `OverlayStore`. `OverlayHost` é montado uma vez, no `body`, e renderiza a pilha.
  Evidência: `_frontend/v8/src/overlays/OverlayHost.vue:19`,
  `_frontend/v8/src/overlays/OverlayStore.js:31`.
- V8-OVL-011 [implementado] ESC e clique fora atuam só no overlay do topo. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:314`.
- V8-OVL-012 [implementado] Fechar um overlay fecha antes os que estão acima dele. Evidência:
  `_frontend/v8/src/overlays/OverlayStore.js:161`.

### Comportamento de todo overlay modal

Vale para modals e para drawers em modo `overlay`.

- V8-OVL-020 [implementado] O overlay é renderizado no `body`, por `<Teleport>`. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:7`.
- V8-OVL-021 [implementado] O foco entra no overlay ao abrir e não sai dele por Tab enquanto ele for
  o topo. Ao fechar, o foco volta ao elemento que o abriu. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:24`.
- V8-OVL-022 [implementado] Enquanto há overlay modal aberto, a página atrás não rola, não recebe
  clique nem foco e fica oculta para leitores de tela. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:12`.
- V8-OVL-023 [implementado] O overlay tem `role="dialog"`, `aria-modal="true"` e `aria-labelledby`
  apontando para o título. O confirm usa `role="alertdialog"`. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:30`.
- V8-OVL-024 [implementado] Um overlay marcado como alterado (`setDirty(true)`) pede confirmação
  antes de fechar por ESC, clique fora, botão de fechar ou botão voltar. Recusada a confirmação, ele
  continua aberto e a URL não muda. Evidência: `_frontend/v8/src/overlays/OverlayStore.js:172`,
  `_frontend/v8/src/overlays/urlSync.js:42`.
- V8-OVL-025 [implementado] Com algum overlay marcado como alterado, sair da página dispara o aviso
  nativo do navegador. Evidência: `_frontend/v8/src/overlays/OverlayHost.vue:83`.
- V8-OVL-026 [implementado] Entrada e saída usam `<Transition>`. Com `prefers-reduced-motion:
  reduce`, não há animação. O drawer guardado na rota entra animado e sai sem animação. Evidência:
  `_frontend/v8/src/css/overlays.css:167`, `_frontend/v8/src/css/tokens.css:38`.

### Drawer

- V8-OVL-030 [implementado] Há um único componente `Drawer`, com `side` (`left`, `right`), `mode`
  (`overlay`, `push`, `docked`), `size` (`sm`, `md`, `lg` ou uma medida CSS) e `scrim` (liga ou
  desliga o fundo escurecido). Evidência: `_frontend/v8/src/overlays/Drawer.vue:15`,
  `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-031 [implementado] O drawer tem cabeçalho com título e botão de fechar, corpo com rolagem
  própria e rodapé de ações fixo. Evidência: `_frontend/v8/src/overlays/OverlayFooter.vue:18`,
  `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-032 [implementado] `push` e `docked` não são modais: não prendem o foco, não bloqueiam a
  página, não entram na pilha e usam `role="complementary"`. Em `push` o conteúdo da página se
  desloca; em `docked` o drawer faz parte do layout. Evidência:
  `_frontend/v8/src/css/overlays.css:128`, `_frontend/v8/src/overlays/OverlayFrame.vue:133`.
- V8-OVL-033 [implementado] Um drawer pode declarar um modo para tela larga e outro para tela
  estreita, como `docked` e `overlay`. Ao cruzar a largura de corte ele troca de modo sem perder o
  conteúdo nem o estado. Evidência: `_frontend/v8/src/overlays/Drawer.vue:42`,
  `_frontend/v8/src/overlays/Encaixe.vue:9`.
- V8-OVL-034 [implementado] Drawers empilhados do mesmo lado aparecem deslocados, de modo que a
  borda de cada um abaixo do topo continue visível. Evidência:
  `_frontend/v8/src/css/overlays.css:91`, `_frontend/v8/src/overlays/OverlayStore.js:54`.

### Conteúdo do drawer e do modal

- V8-OVL-040 [implementado] O conteúdo pode ser um componente Vue importado sob demanda, um
  fragmento HTML buscado em `/v8/_frag/...` ou um elemento já presente na página. Evidência:
  `_frontend/v8/src/overlays/ConteudoEntrada.vue:43`,
  `_frontend/v8/src/overlays/FragmentContent.vue:30`.
- V8-OVL-041 [implementado] Enquanto o componente ou o fragmento carrega, o overlay já está aberto e
  mostra estado de carregamento. Falha mostra mensagem de erro e opção de tentar de novo, dentro do
  overlay. Evidência: `_frontend/v8/src/overlays/ConteudoEntrada.vue:43`,
  `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-042 [implementado] Em fragmento, o texto de `[data-overlay-title]` vira o título do
  overlay. Sem ele, vale o título informado pelo gatilho, e sem este, o texto do gatilho. Evidência:
  `_frontend/v8/src/core/triggers.js:57`, `_frontend/v8/src/overlays/FragmentContent.vue:30`.
- V8-OVL-043 [implementado] Elemento da página usado como conteúdo é movido para dentro do overlay
  ao abrir e devolvido ao lugar de origem ao fechar. Evidência:
  `_frontend/v8/src/overlays/ElementContent.vue:14`, `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-044 [implementado] Ilhas e gatilhos declarativos dentro de um fragmento funcionam como na
  página. Evidência: `_frontend/v8/src/overlays/useDrawer.js:5`.

### Drawer e URL

- V8-OVL-050 [implementado] Em página Django, o drawer de painel fica na query string `painel`, um
  valor por drawer aberto, na ordem da pilha. O valor é `<nome>:<argumento>`, resolvido pelo
  registro de painéis, ou `frag:<caminho>`, resolvido para `/v8/_frag/<caminho>/`. Evidência:
  `_frontend/v8/src/core/paineis.js:1`, `_frontend/v8/src/overlays/alvo.js:1`.
- V8-OVL-051 [implementado] Abrir um painel acrescenta uma entrada ao histórico. O botão voltar
  fecha o drawer, e o avançar reabre. Evidência: `_frontend/v8/src/overlays/urlSync.js:6`,
  `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-052 [implementado] Abrir a página com `painel` na URL abre os drawers correspondentes, na
  mesma ordem. Evidência: `_frontend/v8/src/overlays/urlSync.js:6`,
  `_frontend/v8/src/overlays/useDrawer.js:5`.
- V8-OVL-053 [implementado] Em zona SPA, o drawer é uma rota aninhada: a rota filha renderiza dentro
  do drawer, com lado e tamanho em `meta.drawer`. Fechar leva à rota pai, e rota filha de rota filha
  empilha. Evidência: `_frontend/v8/src/modules/demo/zona.js:5`,
  `_frontend/v8/src/overlays/DrawerRota.vue:17`.
- V8-OVL-054 [implementado] Os dois mecanismos usam o mesmo `Drawer` e a mesma pilha. O que muda é
  só quem guarda o estado: a query string ou a rota. Evidência:
  `_frontend/v8/src/overlays/useDrawer.js:5`.

### Modals

- V8-OVL-060 [implementado] `confirm(opcoes)` devolve uma Promise que resolve `true` ao confirmar e
  `false` ao cancelar ou dispensar. Evidência: `_frontend/v8/src/overlays/ModalConfirm.vue:25`,
  `_frontend/v8/src/overlays/OverlayStore.js:134`.
- V8-OVL-061 [implementado] `openModal(componente, props, opcoes)` devolve uma Promise que resolve
  com o valor passado a `close(valor)` e com `undefined` ao dispensar. A Promise não rejeita por
  dispensa. Evidência: `_frontend/v8/src/overlays/useModal.js:4`.
- V8-OVL-062 [implementado] O componente aberto obtém por `useOverlay()` as funções `close`,
  `dismiss`, `setDirty` e `setTitle` do próprio overlay. Evidência:
  `_frontend/v8/src/overlays/useModal.js:4`, `_frontend/v8/src/overlays/useOverlay.js:3`.
- V8-OVL-063 [implementado] Há quatro tipos padrão: `confirm`, `form`, `wizard` e `fullscreen`. O
  componente de cada modal é importado sob demanda. Evidência:
  `_frontend/v8/src/overlays/useModal.js:4`.
- V8-OVL-064 [implementado] O modal `form` envia pelo cliente de `http.md`. Em erro de validação ele
  continua aberto, mostra cada erro junto ao campo e os erros gerais no topo, e põe o foco no
  primeiro campo com erro. Em sucesso, fecha e resolve com a resposta. Evidência:
  `_frontend/v8/src/overlays/ErrosGerais.vue:18`, `_frontend/v8/src/overlays/useFormModal.js:5`.
- V8-OVL-065 [implementado] O modal `form` se marca como alterado ao primeiro campo editado e deixa
  de estar após salvar. Durante o envio, o botão de salvar fica desabilitado. Evidência:
  `_frontend/v8/src/overlays/useFormModal.js:5`, `_frontend/v8/src/overlays/useModal.js:4`.
- V8-OVL-066 [implementado] O modal `wizard` recebe uma lista de passos, cada um com componente
  próprio e validação. Só avança com o passo válido, permite voltar sem perder o preenchido e
  resolve com os dados reunidos ao concluir. Evidência:
  `_frontend/v8/src/overlays/ModalWizard.vue:63`, `_frontend/v8/src/overlays/useModal.js:4`.
- V8-OVL-067 [implementado] O modal `fullscreen` ocupa toda a janela e segue as regras de todo
  overlay modal. Evidência: `_frontend/v8/src/overlays/useModal.js:4`.

### Toasts

- V8-OVL-070 [implementado] `useToast()` oferece `success`, `info`, `warning` e `error`. Os toasts
  aparecem na camada `--z-toast`, em fila, com no máximo quatro visíveis. Evidência:
  `_frontend/v8/src/overlays/useToast.js:4`.
- V8-OVL-071 [implementado] Toast some sozinho após o tempo do seu nível, e a contagem pausa com o
  ponteiro ou o foco sobre ele. O de erro só some ao ser dispensado. Evidência:
  `_frontend/v8/src/overlays/ToastHost.vue:76`, `_frontend/v8/src/overlays/ToastStore.js:11`.
- V8-OVL-072 [implementado] Toast usa `role="status"`, e o de erro, `role="alert"`. Evidência:
  `_frontend/v8/src/overlays/ToastHost.vue:14`.
- V8-OVL-073 [implementado] No boot, cada mensagem de `#v8-messages` vira um toast do nível
  correspondente. Evidência: `_frontend/v8/src/overlays/mensagens.js:6`.

### Gatilhos em HTML

- V8-OVL-080 [implementado] `main.js` registra um único ouvinte de clique no documento para os
  atributos `data-drawer`, `data-modal` e `data-confirm`. Elementos inseridos depois funcionam sem
  novo registro. Evidência: `_frontend/v8/src/core/triggers.js:9`,
  `_frontend/v8/src/modules/demo/ilhas/ClientesTabela.vue:79`.
- V8-OVL-081 [implementado] `data-drawer="<alvo>"` abre um drawer. O alvo é `<nome>:<argumento>`,
  `frag:<caminho>` ou `el:#<id>`. `data-drawer-side`, `data-drawer-size`, `data-drawer-mode` e
  `data-drawer-title` ajustam o drawer. Evidência: `_frontend/v8/src/core/triggers.js:9`,
  `_frontend/v8/src/overlays/alvo.js:1`.
- V8-OVL-082 [implementado] `data-modal="<alvo>"` abre um modal, com alvo `<nome>:<argumento>` do
  registro de modals ou `frag:<caminho>`. Evidência: `_frontend/v8/src/core/modais.js:1`,
  `_frontend/v8/src/core/triggers.js:9`.
- V8-OVL-083 [implementado] `data-confirm="<mensagem>"` em link, botão ou formulário pede
  confirmação. Confirmada, a ação original segue: o link é seguido ou o formulário é enviado.
  Evidência: `_frontend/v8/src/core/triggers.js:9`.
- V8-OVL-084 [implementado] O gatilho é um link ou botão que funciona sem JavaScript: o `href` leva
  a uma página com o mesmo conteúdo, e o formulário envia normalmente. Evidência:
  `_frontend/v8/src/core/triggers.js:9`.
- V8-OVL-085 [implementado] Clique com Ctrl, Cmd, Shift ou botão do meio não é interceptado.
  Evidência: `_frontend/v8/src/core/triggers.js:9`.

### Fragmentos no servidor

- V8-OVL-090 [implementado] Uma view de fragmento devolve só o HTML do fragmento, sem layout, a
  partir de um template de `v8/partials/`. Evidência: `cmj/v8/views.py:128`.
- V8-OVL-091 [implementado] Por padrão o fragmento sai com `Cache-Control: private`. Só sai `public`
  o fragmento que a view declara público e que não exige autenticação. Evidência:
  `cmj/v8/views.py:143`.
- V8-OVL-092 [implementado] Requisição de fragmento sem autenticação, quando a view a exige, recebe
  401 em JSON, e não redirecionamento. Evidência: `cmj/v8/views.py:93`.

## Requisitos de segurança

- V8-OVL-100 [implementado] O valor de `painel`, de `data-drawer` e de `data-modal` nunca é usado
  como URL. Nome fora do registro é ignorado. Em `frag:<caminho>`, o caminho só aceita letras,
  números, `_`, `-` e `/`, e a busca vai sempre para a mesma origem, sob `/v8/_frag/`. Item da
  varredura: 4. Evidência: `_frontend/v8/src/overlays/alvo.js:7`,
  `_frontend/v8/src/overlays/urlSync.js:22`.
- V8-OVL-101 [implementado] Cada view de fragmento confere autenticação e permissão por conta
  própria, e filtra pelo usuário os registros que devolve. Abrir o fragmento pela URL direta dá o
  mesmo resultado que abri-lo pelo drawer. Item da varredura: 1. Evidência: `cmj/v8/views.py:349`.
- V8-OVL-102 [implementado] Fragmento que depende do usuário não usa cache compartilhado de
  resposta. Havendo `{% cache %}`, a chave inclui o usuário ou as permissões de que o conteúdo
  depende. Item da varredura: 5. Evidência: `cmj/v8/views.py:128`,
  `_templates/v8/v8/shell/menu.html:5`.
- V8-OVL-103 [implementado] O HTML do fragmento é inserido sem executar `<script>`, e o template do
  fragmento mantém o autoescape. Item da varredura: 4. Evidência:
  `_frontend/v8/src/overlays/FragmentContent.vue:30`.
- V8-OVL-104 [implementado] Título de overlay, texto de toast e mensagem de confirm são inseridos
  como texto, nunca como HTML, inclusive os vindos de `#v8-messages` e de atributos `data-*`. Item
  da varredura: 4. Evidência: `_frontend/v8/src/overlays/ModalConfirm.vue:25`,
  `_frontend/v8/src/overlays/useToast.js:11`.
- V8-OVL-105 [implementado] `data-confirm` não é proteção: ação que altera estado é `POST` com CSRF
  e o servidor a valida de novo. Nenhuma ação que altera estado é `GET`. Item da varredura: 1.
  Evidência: `cmj/v8/views.py:310`.
- V8-OVL-106 [implementado] A resposta de fragmento leva `X-Robots-Tag: noindex`. Item da varredura:
  5. Evidência: `cmj/v8/views.py:141`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-21. Os overlays não alcançam código legado.

## Dúvidas

Nenhuma. A escolha entre construir do zero e usar biblioteca está em D2 de `arquitetura.md`.

## Fora do escopo

- Enviar por JavaScript um formulário que está dentro de um fragmento HTML e trocar o fragmento
  pela resposta. Esse formulário envia como navegação normal.
- Drawer arrastável ou redimensionável pelo usuário.
- Sincronizar modals com a URL.
