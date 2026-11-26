# V8: arquitetura híbrida

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `6b527f42a`)
Código principal: `cmj/v8/`, `_templates/v8/`, `_frontend/v8/src/core/`, `_frontend/v8/src/stores/`
Testes: `cmj/v8/tests/test_arquitetura.py`, `_frontend/v8/tests/core/`, `_frontend/v8/tests/stores/`

O Django continua dono das rotas e renderiza o que puder no servidor. O Vue tem o próprio mapa de
rotas e entra só onde a página pede: numa ilha ou numa zona SPA. A página tem sempre um único app
Vue e um único Pinia.

## Escopo

App novo `cmj/v8` (`name = "cmj.v8"`, `label = "v8"`), sem models, migrations, signals nem context
processor. O único middleware é o da troca de portal (`portal.md`). Recebe as views, as rotas, as
template tags e os serviços do v8:

| Arquivo | Conteúdo |
| --- | --- |
| `cmj/v8/urls.py` | Todas as rotas `^v8/` |
| `cmj/v8/views.py` | Views de página, de zona, de fragmento e o 404 do v8 |
| `cmj/v8/services/s_global.py` | Dados globais da página e registro das zonas SPA |
| `cmj/v8/services/s_menu.py` | Menu e filtro por permissão (regras em `shell.md`) |
| `cmj/v8/services/s_respostas.py` | Corpos JSON padronizados: erro de validação, 401, 403 e 404 (regras em `http.md`) |
| `cmj/v8/services/s_demo.py` | Dados e validações da demonstração (regras em `demo.md`) |
| `cmj/v8/templatetags/v8_tags.py` | `v8_dados_globais`, `v8_mensagens`, `v8_island`, `v8_menu` |

Arquivos existentes alterados, e só eles:

| Arquivo | Mudança |
| --- | --- |
| `cmj/settings/apps.py` | `"cmj.v8"` em `CMJ_APPS` |
| `cmj/urls.py` | `include(cmj.v8.urls)` antes de `cmj.core.urls` |
| `cmj/core/urls.py`, `cmj/core/views.py` | Saem a rota `^v8/(?P<slug>[^.]*)$` e a view `app_vue_view_v8`, que passam para o app novo |
| `_templates/v8/base_v8.html` | Reescrito como base dos layouts |
| `cmj/settings/middleware.py` | `cmj.v8.middleware.PortalV8Middleware` depois do `AuthenticationMiddleware` (`portal.md`) |
| `_templates/v2018/path/pagina_inicial.html` | `include` do botão "Conferir o novo portal", fora dos fragmentos em cache (`portal.md`) |
| `_frontend/v8/` | `package.json`, `vite.config.js`, `eslint.config.js` e `src/` |

Legado tocado: a rota e a view do v8 em `cmj/core`, que serviam de teste entre o Django e o Vue
Router; e, para a troca de portal (`portal.md`), uma linha da lista de middlewares e um `include`
na página inicial do v2018.

## Regras

### Contenção

- V8-ARQ-001 [implementado] Toda rota de `cmj/v8/urls.py` casa apenas com caminhos iniciados por
  `/v8/`. Evidência: `cmj/v8/urls.py:119`.
- V8-ARQ-002 [implementado] As rotas que já existiam continuam resolvendo para as mesmas views:
  `/v6/<slug>`, `/app/<slug>`, `/v8/service-worker.js`, `/v8/manifest.json`, `/admin/` e o catch-all
  de `cmj.sigad` para caminhos fora de `/v8/`. Evidência: `cmj/urls.py:76`.
- V8-ARQ-003 [implementado] Todo template novo fica em `_templates/v8/v8/` e é referido como
  `v8/...`. Na raiz de `_templates/v8/` só existe `base_v8.html`. Nenhum caminho relativo de
  `_templates/v8` existe em outro diretório de templates do projeto. Motivo: `_templates/v8` vem
  antes de `_templates/v2018` na busca (`cmj/settings/frontend.py:18-32`), e um `base.html` ou
  `404.html` na raiz encobriria os do portal. Evidência: `cmj/v8/tests/test_arquitetura.py:84`.
- V8-ARQ-004 [implementado] Todo cookie criado pelo v8 tem nome iniciado por `v8_` e `Path=/v8/`,
  exceto o `v8_portal`, que tem `Path=/` porque liga o v8 nas rotas do portal (`portal.md`).
  Evidência: `_frontend/v8/src/core/cookies.js:1`.
- V8-ARQ-005 [implementado] Fora de `/v8/`, o frontend só chama o que já existe e sem alterá-lo:
  `/api/version`, `/api/auth/session`, `/api/<app>/<model>/` e `/ws/sync/`. Evidência:
  `_frontend/v8/src/stores/GlobalStore.js:13`.
- V8-ARQ-006 [implementado] `python manage.py makemigrations --check --dry-run` não acusa mudança
  causada pelo app `v8`. Evidência: `cmj/v8/apps.py:5`.

### Rotas Django

- V8-ARQ-010 [implementado] `/v8/` responde 200 com a página inicial no layout `landing`. Evidência:
  `cmj/v8/views.py:176`.
- V8-ARQ-011 [implementado] Cada zona SPA é declarada uma única vez, em `s_global.py`, com nome,
  prefixo e layout. A rota da zona responde 200 com a página da zona, no layout que ela declara,
  para o prefixo e para qualquer subcaminho dele, com ou sem barra final. Evidência:
  `cmj/v8/services/s_global.py:112`, `_frontend/v8/src/core/router.js:35`.
- V8-ARQ-012 [implementado] Caminho `/v8/...` que não é página, zona nem fragmento responde 404, no
  layout `minimal`. Evidência: `cmj/v8/views.py:212`.
- V8-ARQ-013 [implementado] Páginas e fragmentos renderizados pelo Django têm URL terminada em `/`.
  Evidência: `cmj/v8/urls.py:19`.
- V8-ARQ-014 [implementado] As views do v8 só autenticam, validam a entrada, chamam o serviço e
  respondem. Decisões e dados vêm de `cmj/v8/services/`, que recebe o usuário por parâmetro e nunca
  o `request`. Evidência: `cmj/v8/services/s_global.py:266`, `cmj/v8/views.py:65`.

### Templates

As camadas de templates, os blocks de cada nível e os layouts estão em `templates.md`.

- V8-ARQ-020 [retirada] Substituída por V8-TPL-011 e V8-TPL-012.
- V8-ARQ-021 [retirada] Substituída por V8-TPL-002.
- V8-ARQ-022 [implementado] Um template que estende um layout do v8 renderiza sem erro tendo no
  contexto apenas o que os context processors fornecem. O que faltar, as tags do v8 calculam.
  Evidência: `cmj/v8/templatetags/v8_tags.py:40`.
- V8-ARQ-023 [implementado] `{% v8_dados_globais %}` emite `<script id="v8-global"
  type="application/json">` com exatamente estas chaves: `versao`, `debug`, `autenticado`, `usuario`
  (`null` ou `id`, `username`, `nome`, `avatar`), `permissoes` (lista ordenada), `urls` (`api`,
  `versao`, `sessao`, `login`, `logout`, `base`, `frag`), `zonas` (nome para prefixo), `zona` (a da
  página ou `null`), `flags`, `tema`, `modo` e `sidebar`. O conteúdo vem de `s_global.dados_globais`. Como o
  login do portal é o e-mail, `username` é só a parte antes do `@`, e `nome` usa esse valor quando o
  usuário não tem nome completo. Evidência: `cmj/v8/services/s_global.py:266`,
  `cmj/v8/templatetags/v8_tags.py:69`.
- V8-ARQ-024 [implementado] `{% v8_mensagens %}` emite `<script id="v8-messages"
  type="application/json">` com a lista das mensagens do `django.contrib.messages`, cada uma com
  `nivel` e `texto`. Sem mensagens, a lista é vazia. Evidência: `cmj/v8/templatetags/v8_tags.py:80`.
- V8-ARQ-025 [implementado] Dados de uma página vão no bloco `page_data`, sempre por `json_script`.
  Evidência: `_templates/v8/base_v8.html:18`.
- V8-ARQ-026 [implementado] O conteúdo do bloco `content` é HTML do servidor e é legível e navegável
  com o JavaScript desligado. Evidência: `_templates/v8/v8/demo/clientes.html:43`.
- V8-ARQ-027 [implementado] As páginas renderizam o mesmo HTML com `DummyCache` e com cache real.
  Todo `{% cache %}` tem na chave tudo de que o trecho depende. Evidência:
  `_templates/v8/v8/shell/menu.html:5`.

### App Vue único

- V8-ARQ-030 [implementado] `main.js` é o único entry do Vite e cria um app Vue e um Pinia por
  página. Uma segunda execução do boot não cria outro. Evidência:
  `_frontend/v8/src/core/boot.js:12`, `_frontend/v8/src/core/pinia.js:3`.
- V8-ARQ-031 [implementado] O app é montado em `#cmj-v8-app`, que o Django entrega vazio. O HTML do
  Django nunca é compilado como template Vue, e o build não inclui o compilador de templates.
  Evidência: `_frontend/v8/src/App.vue:9`.
- V8-ARQ-032 [implementado] `GlobalStore` lê `#v8-global` uma vez no boot, e `AuthStore` nasce
  preenchido por ele, sem requisição. JSON ausente ou inválido resulta em usuário anônimo, sem
  exceção. Evidência: `_frontend/v8/src/stores/AuthStore.js:14`,
  `_frontend/v8/src/stores/GlobalStore.js:3`.
- V8-ARQ-033 [implementado] Cada `[data-vue-island="<nome>"]` recebe o componente registrado com
  esse nome, renderizado dentro do app único por `<Teleport>`. As props vêm do `json_script`
  apontado por `data-props-id`. O código de uma ilha só é baixado em página que a contém. Evidência:
  `_frontend/v8/src/core/IslandHost.vue:14`, `_frontend/v8/src/core/ilhas.js:1`.
- V8-ARQ-034 [implementado] O HTML que o Django pôs dentro da ilha fica visível até o componente
  estar pronto, e só então é substituído. Nome desconhecido ou falha ao baixar deixam esse HTML no
  lugar e não afetam as outras ilhas. Evidência: `_frontend/v8/src/core/IslandHost.vue:14`.
- V8-ARQ-035 [implementado] Ilha presente em HTML inserido depois do boot, como um fragmento num
  drawer, é montada ao entrar na página e desmontada ao sair. Evidência:
  `_frontend/v8/src/core/IslandHost.vue:14`.
- V8-ARQ-036 [implementado] `{% v8_island "nome" props %}...{% endv8_island %}` emite o elemento da
  ilha, o `json_script` das props com id único na página e o conteúdo do bloco como HTML de espera.
  Evidência: `cmj/v8/templatetags/v8_tags.py:146`.
- V8-ARQ-037 [implementado] Há um único Vue Router. Numa página de zona, o boot importa só o módulo
  de rotas daquela zona e o registra sob o prefixo lido de `#v8-global`. O `<RouterView>` aparece em
  `[data-vue-zone]`. Evidência: `_frontend/v8/src/core/ZoneOutlet.vue:30`,
  `_frontend/v8/src/core/router.js:6`.
- V8-ARQ-038 [implementado] Navegação para um caminho da zona atual é feita pelo Vue Router, sem
  recarregar. Navegação para qualquer outro caminho é carga normal de página. Em página sem zona, o
  router só altera a query string. Evidência: `_frontend/v8/src/core/router.js:6`.
- V8-ARQ-039 [implementado] Caminho desconhecido dentro de uma zona mostra `Error404.vue` no lugar
  do miolo, com o shell intacto. Evidência: `_frontend/v8/src/core/router.js:6`.
- V8-ARQ-040 [implementado] Componentes de rota, de ilha, de modal e de painel são importados sob
  demanda. Evidência: `_frontend/v8/src/core/ilhas.js:4`, `_frontend/v8/src/core/zonas.js:7`.
- V8-ARQ-041 [implementado] O WebSocket `/ws/sync/` só é aberto quando algum componente usa o
  `SyncStore`. Evidência: `_frontend/v8/src/stores/SyncStore.js:22`.

### CSS

- V8-ARQ-050 [implementado] O CSS é gerado pelo Tailwind v4 (`@tailwindcss/vite`), que lê as classes
  de `_frontend/v8/src` e de `_templates/v8`. Evidência: `_frontend/v8/src/css/app.css:8`,
  `_frontend/v8/vite.config.js:37`.
- V8-ARQ-051 [retirada] Cores, espaçamentos de layout, durações de animação e camadas de z-index
  eram tokens declarados em um único arquivo, `src/css/tokens.css`. Substituída por V8-TEMA-011.
- V8-ARQ-052 [implementado] Os primitivos de overlay, popover e tooltip vêm do Reka UI. Evidência:
  `_frontend/v8/src/overlays/OverlayFrame.vue:137`.

### Restos do v6

- V8-ARQ-055 [implementado] Saem do v8: a inicialização de `bootstrap.Popover` em `main.js`, os
  globais `bootstrap` e `EventBus` do ESLint, `data-bs-theme`, a regra `fortawesome` de
  `manualChunks`, `src/sw.js` e `registerComponents.js`. Evidência:
  `_frontend/v8/eslint.config.js:13`, `_frontend/v8/vite.config.js:168`.

## Requisitos de segurança

- V8-ARQ-060 [implementado] `#v8-global` contém só as chaves de V8-ARQ-023. Não contém e-mail, CPF,
  telefone, token, id de sessão nem dados de outro usuário. Para anônimo, `usuario` é `null` e
  `permissoes` é vazia. Item da varredura: 2. Evidência: `cmj/v8/services/s_global.py:244`.
- V8-ARQ-061 [implementado] `#v8-global` e `#v8-messages` nunca ficam dentro de `{% cache %}`. Toda
  resposta HTML de página do v8 sai com `Cache-Control: private`. Item da varredura: 5. Evidência:
  `cmj/v8/views.py:54`, `_templates/v8/base_v8.html:16`.
- V8-ARQ-062 [implementado] Dado do servidor só chega ao JavaScript por `json_script`. Não há
  `<script>` com valor interpolado nem `|safe` sobre dado de usuário. Um valor com `</script>`,
  aspas e `&` chega ao store idêntico ao original. Item da varredura: 4. Evidência:
  `cmj/v8/templatetags/v8_tags.py:76`.
- V8-ARQ-063 [implementado] Texto com `{{ }}` ou `[[ ]]` vindo do servidor aparece literal e nunca é
  avaliado pelo Vue. Item da varredura: 4. Evidência: `_frontend/v8/src/core/boot.js:39`.
- V8-ARQ-064 [implementado] O nome em `data-vue-island` e o nome da zona só são resolvidos pelos
  registros do frontend. Nenhum caminho de importação é montado a partir de atributo, URL ou JSON.
  Item da varredura: 4. Evidência: `_frontend/v8/src/core/IslandHost.vue:90`,
  `_frontend/v8/src/core/ilhas.js:2`.
- V8-ARQ-065 [implementado] As permissões no navegador servem só para esconder o que o servidor
  recusaria. Toda view e todo endpoint do v8 conferem autenticação e permissão no servidor. Item da
  varredura: 1. Evidência: `cmj/v8/views.py:65`.
- V8-ARQ-066 [implementado] Views de página, de zona e de fragmento aceitam só `GET` e `HEAD`. Outro
  método recebe 405. Item da varredura: 1. Evidência: `cmj/v8/views.py:130`.
- V8-ARQ-067 [implementado] Valor de cookie do v8 só é aceito se estiver na lista de valores válidos
  daquele cookie. Fora dela, vale o padrão. Os cookies não guardam dado sensível, têm `SameSite=Lax`
  e, fora de DEBUG, `Secure`. Item da varredura: 6. Evidência: `_frontend/v8/src/core/cookies.js:1`.
- V8-ARQ-068 [implementado] O subcaminho capturado pela rota de zona não escolhe template nem
  arquivo e não é renderizado. A página 404 do v8 não reproduz o caminho pedido. Itens da varredura:
  3 e 4. Evidência: `cmj/v8/views.py:185`, `cmj/v8/views.py:115`.
- V8-ARQ-069 [implementado] Página do v8 acessível a anônimo não dispara PDF, IA, OCR nem task. Item
  da varredura: 7. Evidência: `cmj/v8/views.py:176`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7 no legado alcançado (a rota `^v8/` e a view
`app_vue_view_v8` de `cmj/core`), em 2026-11-21, por leitura do código.

## Dúvidas

- D1. Views de fragmento, catch-all por zona e menu por permissão pedem Python. Opções: só
  templates, ou um app isolado. Decisão (2026-11-21): app novo `cmj/v8`, contido em `/v8/`, e a
  rota e a view do v8 saem de `cmj/core`.
- D2. Base dos overlays e do CSS. Decisão (2026-11-21): Reka UI e Tailwind v4.
- D3. Hoje o v8, como o v6, compila no navegador o HTML do Django como template Vue (`<cmj-app>`,
  `[[ ]]`). Recomendação: abandonar isso no v8 e montar o app em um elemento próprio, o que tira o
  compilador do build e impede que texto do servidor seja avaliado. `App.vue` vira a raiz do app
  único. Alternativa: manter o modelo do v6. Decisão (2026-11-21): app em elemento próprio; o v8
  deixa de compilar o HTML do Django.
- D4. O v8 não tem testes de frontend. Recomendação: Vitest, `@vue/test-utils` e jsdom como
  `devDependencies`, com testes em `_frontend/v8/tests/` e `npm run test`. Alternativa: testar só o
  lado Django com pytest. Decisão (2026-11-21): Vitest, `@vue/test-utils` e jsdom. O que o DOM
  simulado não cobre de foco e rolagem é verificado à mão na demonstração.
- D5. Hoje toda página do v8 abre o WebSocket `/ws/sync/` e faz `GET /api/version`. Recomendação:
  preencher o `AuthStore` pelo JSON global e abrir o WebSocket só no primeiro uso. Alternativa:
  manter os dois no boot. Decisão (2026-11-21): sob demanda.

## Fora do escopo

- Migrar telas do v6 ou do v2018, e criar telas reais além da demonstração.
- Mudar o service worker e o manifesto do PWA.
- Testes de navegador de ponta a ponta.
