# V2018: estrutura do projeto

Status: observado, com uma regra acordada (V2018-EST-060, a política de manutenção) e quatro implementadas (V2018-EST-016, 042, 043 e 044)
Última verificação: 2026-11-21 (commit `dc27ae6d6`)
Código principal: `_frontend/v2018/vue.config.js`, `_frontend/v2018/package.json`, `_frontend/v2018/src/`, `cmj/settings/frontend.py`, `cmj/globalrules/views.py`, `_templates/v2018/base.html`
Testes: `_frontend/v2018/tests/`, `cmj/globalrules/tests/test_service_worker.py`

Como o projeto é montado: um build webpack com várias entradas, em que uma aplicação Vue convive
com módulos independentes, e como o Django carrega cada parte. Obtido por leitura do código, salvo
onde a regra diz outra coisa.

## Escopo

- Build e dev server: `vue.config.js` e `package.json`.
- Integração com o Django: `webpack_loader`, templates base e rotas que entregam os bundles.
- Aplicação principal (entrada `app`): como sobe e quais são as peças comuns.
- Módulos independentes (demais entradas): que existem, como sobem e do que dependem.

A spec registra que os módulos existem. Não descreve o que cada um faz.

## Regras

### Build

- V2018-EST-001 [observado] O projeto usa Vue 2.7 com Vue CLI 5 sobre webpack 5. Os scripts são
  `serve`, `build`, `lint` e `test`. Evidência: `_frontend/v2018/package.json:8`.
- V2018-EST-002 [observado] O build tem cinco entradas: `app`, que é a padrão do Vue CLI
  (`src/main.js`), e `construct`, `compilacao`, `loa` e `libsuserauth`, cada uma com o próprio
  `main.js`. Evidência: `_frontend/v2018/vue.config.js:62-76`.
- V2018-EST-003 [retirada] Removida: a pasta `src/__apps/painel`, que não era entrada do build, foi
  apagada (D2). Toda pasta de `src/__apps` com `main.js` é entrada, conforme V2018-EST-002.
- V2018-EST-004 [observado] O webpack fornece `$`, `jQuery`, `window.jQuery` e `_` a todo arquivo,
  sem import. Evidência: `_frontend/v2018/vue.config.js:79`.
- V2018-EST-005 [observado] O alias `@` aponta para `src/` (padrão do Vue CLI), e imports de
  componente omitem a extensão `.vue`. Evidência: `_frontend/v2018/src/App.vue:10`.
- V2018-EST-006 [observado] O Vue é empacotado com o compilador de templates
  (`runtimeCompiler: true`). Evidência: `_frontend/v2018/vue.config.js:24`.
- V2018-EST-007 [observado] A saída vai para `dist/v2018`. O caminho público é `/static/v2018` em
  produção e `http://<DEV_HOST_NAME>:8080/` em desenvolvimento. Evidência:
  `_frontend/v2018/vue.config.js:25-26`.
- V2018-EST-008 [observado] O runtime do webpack fica num chunk único, comum às entradas. Em
  produção, cada pacote de `node_modules` vira um chunk `npm.<pacote>`. Evidência:
  `_frontend/v2018/vue.config.js:60`, `_frontend/v2018/vue.config.js:133`.
- V2018-EST-009 [observado] O build grava a lista de chunks de cada entrada em `webpack-stats.json`
  (produção) ou `dev-webpack-stats.json` (desenvolvimento). O build de produção apaga o
  `dev-webpack-stats.json`. Evidência: `_frontend/v2018/vue.config.js:91`,
  `_frontend/v2018/vue.config.js:131`.
- V2018-EST-010 [observado] `src/assets` é copiado para a raiz da saída, e os skins do TinyMCE para
  `js/skins`. Evidência: `_frontend/v2018/vue.config.js:94`.
- V2018-EST-011 [observado] Só o build de produção remove `console.*`, gera `.gz`, o manifesto PWA
  e o `service-worker.js` (Workbox, a partir de `src/service-worker.js`). Evidência:
  `_frontend/v2018/vue.config.js:154`, `_frontend/v2018/vue.config.js:193`.
- V2018-EST-012 [observado] `vue.config.js` lê do `.env` do backend (`../../cmj/.env`) só
  `DEV_HOST_NAME` e `DEV_BACKENDPORT`. O restante do arquivo não entra no ambiente do processo do
  dev server nem do build. Evidência: `_frontend/v2018/vue.config.js:15-21`.
- V2018-EST-013 [observado] O dev server escuta em todas as interfaces, na porta 8080, aceita
  qualquer `Host` e responde com `Access-Control-Allow-Origin: *`. Evidência:
  `_frontend/v2018/vue.config.js:29-37`.
- V2018-EST-014 [retirada] Substituída por V2018-EST-015. O `package-lock.json` passou a ser
  versionado (D7).
- V2018-EST-015 [observado] `package-lock.json`, `dist/v2018` e `webpack-stats.json` são
  versionados. O rebuild apaga o lock, roda `npm install`, que mantém as versões já presentes em
  `node_modules`, e commita o lock novo junto com o `dist/`: o lock do repositório diz quais versões
  geraram o build em produção. O CI instala com `npm ci`. Evidência:
  `.github/workflows/ci.yml:54-55`.
- V2018-EST-016 [implementado] Os três frontends têm `.npmrc` com `min-release-age=7`: o npm só
  instala versões publicadas há mais de 7 dias, inclusive no rebuild. Evidência:
  `_frontend/v2018/.npmrc:2`.

### Integração com o Django

- V2018-EST-020 [observado] O Django lê os chunks pelo `webpack_loader`. Com `DEBUG`, usa
  `dev-webpack-stats.json` se o arquivo existir, e `webpack-stats.json` se não existir. Sem
  `DEBUG`, usa sempre `webpack-stats.json`. Evidência: `cmj/settings/frontend.py:111-121`,
  `cmj/settings/frontend.py:162-166`.
- V2018-EST-021 [observado] `base.html` carrega a entrada `app` em toda página que o estende, e a
  entrada `libsuserauth` só quando o usuário está autenticado. Evidência:
  `_templates/v2018/base.html:20-23`, `_templates/v2018/base.html:145-148`.
- V2018-EST-022 [observado] `base.html` põe `<div id="app"><App/></div>` no bloco `appvue_content`.
  Templates filhos esvaziam o bloco ou trocam o conteúdo de `#app`. Evidência:
  `_templates/v2018/base.html:119-121`, `_templates/v2018/path/path_pntp.html:27-34`.
- V2018-EST-023 [observado] `/app/<slug>` entrega `app_vue_v2018.html`, que só tem o `#app` e a
  entrada `app`. Evidência: `cmj/core/urls.py:116`, `cmj/core/views.py:103-104`.
- V2018-EST-024 [observado] Os templates de CRUD carregam a entrada cujo nome está em
  `view.crud.frontend`. O padrão é vazio, e só views de `cmj/loa` o definem, com `loa`. Evidência:
  `sapl/crud/base.py:1091`, `_templates/v2018/crud/form.html:8`.
- V2018-EST-025 [observado] Toda entrada é pedida por algum template: `construct` em
  `sigad/documento_construct.html`, `compilacao` em `compilacao/base_compilacao.html` e
  `norma/normajuridica_detail.html`, `loa` pelos templates de CRUD. Evidência:
  `_templates/v2018/sigad/documento_construct.html:17`,
  `_templates/v2018/compilacao/base_compilacao.html:11`.
- V2018-EST-026 [retirada] Substituída por V2018-EST-029. Os templates que pediam os bundles
  `global`, `painel` e `draft`, que não eram entradas, foram removidos (D1).
- V2018-EST-027 [observado] `/service-worker.js` é servido pelo Django a partir de
  `dist/v2018/service-worker.js`, com `Service-Worker-Allowed: /`. Evidência:
  `cmj/globalrules/urls.py:16`, `cmj/globalrules/views.py:72-75`.
- V2018-EST-044 [implementado] Com `DEBUG`, a view do service worker tenta antes o dev server, no
  endereço que vem da configuração: `DEV_HOST_NAME` ou, quando o acesso é pela porta publicada do
  container do backend (9099), o container do frontend. O host pedido não entra na URL consultada.
  Sem `DEBUG`, nenhum dev server é consultado. Vale para v2018, v6 e v8. Evidência:
  `cmj/globalrules/views.py:46-55`.
- V2018-EST-028 [observado] Sem `DEBUG`, `dist/` do v2018 entra em `STATICFILES_DIRS`, e os arquivos
  saem em `/static/v2018/`. Evidência: `cmj/settings/frontend.py:154-159`.

- V2018-EST-029 [observado] Todo bundle pedido por nome literal num template é uma entrada do
  build. Um nome que não é entrada faz o `webpack_loader` falhar com `WebpackBundleLookupError`
  (verificação local, sem escrita, em 2026-11-21). Evidência:
  `_frontend/v2018/tests/estrutura/entradas.spec.js:90`.

### Aplicação principal (entrada `app`)

- V2018-EST-030 [observado] `src/main.js` cria um único `new Vue` em `#app`, com delimitadores
  `[[ ]]`, Vue Router em modo `history` e a store Vuex. O HTML que o Django deixou dentro de `#app`
  é compilado como template. O componente `App` consulta `/api/version` ao montar. Evidência:
  `_frontend/v2018/src/main.js:46-51`, `_frontend/v2018/src/App.vue:16-18`.
- V2018-EST-031 [observado] Toda entrada que usa jQuery começa importando
  `expose-global-jquery`, que põe o jQuery em `window.$` e `window.jQuery` para os scripts dos
  templates Django. Evidência: `_frontend/v2018/src/expose-global-jquery.js:2`.
- V2018-EST-032 [observado] As rotas do Vue ficam em `src/routers.js`, todas sob `/loa/`, com
  componentes carregados sob demanda. Evidência: `_frontend/v2018/src/routers.js:6-34`.
- V2018-EST-033 [observado] A store tem os módulos `store__auth`, `store__message`,
  `store__online` e `store__sync`. Só `store__sync` tem namespace. Evidência:
  `_frontend/v2018/src/store.js:7-12`, `_frontend/v2018/src/stores/sync/sync.js:6`.
- V2018-EST-034 [observado] `src/mixins.js` aplica um mixin global: todo componente recebe
  `utils`, o cache de dados, as ações comuns e dois listeners do `EventBus` (`user-logged-in` e
  `user-logged-out`), registrados em `created` e removidos em `beforeDestroy`. Evidência: `_frontend/v2018/src/mixins.js:9`,
  `_frontend/v2018/src/mixins.js:179-187`.
- V2018-EST-035 [observado] `src/registerComponents.js` registra como globais `App` e os
  componentes de `src/modules/pntp`. Evidência: `_frontend/v2018/src/registerComponents.js:11-18`.
- V2018-EST-036 [observado] O acesso HTTP passa por `Resources.Utils` (`src/resources/index.js`),
  com axios, base `/api`, CSRF pelo cookie `csrftoken` e cabeçalho `X-CSRFToken`, e GET sem cache.
  Evidência: `_frontend/v2018/src/resources/index.js:2-11`.
- V2018-EST-037 [retirada] Substituída por V2018-EST-041. Os dois clientes WebSocket declarados e
  nunca abertos foram removidos (D4).
- V2018-EST-038 [observado] O service worker só é registrado em produção, com escopo `/`. Ele
  guarda em cache os arquivos do build e deixa passar direto para a rede os caminhos iniciados por
  `/api`, `/admin`, `/v6` e `/dash`. Evidência: `_frontend/v2018/src/registerServiceWorker.js:3-7`,
  `_frontend/v2018/src/service-worker.js:7-27`.
- V2018-EST-039 [observado] `src/__globals` é carregado pela entrada `app` e vale para toda página:
  o SCSS do portal, as bibliotecas jQuery (Bootstrap 4, bootstrap-select, jQuery UI, máscaras),
  funções publicadas em `window` e inicializações executadas no `ready` do documento. Evidência:
  `_frontend/v2018/src/__globals/index.js:1-2`, `_frontend/v2018/src/__globals/js/index.js:1`,
  `_frontend/v2018/src/__globals/js/importlibs/index.js:8-11`.
- V2018-EST-040 [observado] `src/modules/` (`loa` e `pntp`) e `src/components/` fazem parte da
  entrada `app`: chegam pelas rotas ou pelo registro global. Evidência:
  `_frontend/v2018/src/routers.js:9`, `_frontend/v2018/src/registerComponents.js:3`.

- V2018-EST-041 [observado] O v2018 não tem cliente WebSocket: as telas com atualização em tempo
  real estão no v6. `store__sync` guarda só `data_cache`, o cache dos dados buscados por HTTP com
  `fetchSync`. Evidência: `_frontend/v2018/src/stores/sync/sync.js:5-9`.

- V2018-EST-042 [implementado] O componente de mensagens da entrada `app` exibe o texto da
  mensagem como texto, sem interpretar HTML. Evidência:
  `_frontend/v2018/src/components/utils/message/Message.vue:11`.

- V2018-EST-043 [implementado] Dentro do elemento em que o Vue é montado (`#app` e `#app-vue`), o
  template Django só escreve tags de componente. Variável do Django só entra como id numérico em
  valor de atributo, e não há tag de template nem texto. Motivo: esse HTML é compilado como template
  Vue (V2018-EST-006 e V2018-EST-030). Evidência: `_templates/v2018/path/path_pntp.html:29-32`.

### Módulos independentes (demais entradas)

- V2018-EST-050 [observado] `src/__construct` é uma segunda aplicação Vue, montada em `#app-vue`,
  com store, rotas e componentes próprios, delimitadores padrão e `vue-resource`. Não usa a store
  nem o mixin da entrada `app`. Evidência: `_frontend/v2018/src/__construct/main.js:52-57`.
- V2018-EST-051 [observado] A entrada `construct` depende do `tinymce` global, que quem define é a
  entrada `libsuserauth`. Sem ela, o editor de texto de `construct` não carrega. Evidência:
  `_frontend/v2018/src/__construct/apps/sigad/components/TpdTexto.vue:40`,
  `_frontend/v2018/src/__apps/libsuserauth/main.js:12`.
- V2018-EST-052 [observado] `src/__apps/loa` não usa Vue: são classes JavaScript sobre jQuery e
  axios. O singleton fica em `window.AppLOA` e só é executado em página que tenha `.container-loa`.
  Evidência: `_frontend/v2018/src/__apps/loa/AppLOA.js:11`,
  `_frontend/v2018/src/__apps/loa/main.js:15-17`.
- V2018-EST-053 [observado] `src/__apps/compilacao` não usa Vue: é jQuery e jQuery UI, com as
  funções publicadas em `window`. Evidência: `_frontend/v2018/src/__apps/compilacao/main.js:18-20`.
- V2018-EST-054 [observado] `src/__apps/libsuserauth` empacota o TinyMCE e publica
  `window.tinymce`, `window.initTextRichEditor` e `window.removeTinymce`. Evidência:
  `_frontend/v2018/src/__apps/libsuserauth/main.js:12-20`.
- V2018-EST-055 [observado] `src/__apps/index.js` só tem um comentário com a intenção da pasta:
  módulos independentes que espelhem os apps do backend. Evidência:
  `_frontend/v2018/src/__apps/index.js:1-7`.

### Política de manutenção

- V2018-EST-060 [acordado] O v2018 não recebe módulo nem entrada totalmente novos. Funcionalidade
  nova que complementa uma tela do v2018 pode ser feita nele quando for urgente e a migração para o
  v6 ou o v8 não couber no prazo. Decisão do responsável em 2026-11-21. Evidência:
  `docs/frontend/v2018.md:7-9`.

## Riscos de segurança

Varredura de 2026-11-21 sobre o build, o dev server, a integração com o Django e as peças comuns
da entrada `app`. O código dos módulos não foi varrido (veja Fora do escopo). Itens 1, 2 e 4 da
varredura não se aplicam: a estrutura não tem view, endpoint nem execução no servidor próprios,
além da view do service worker.

Nenhum risco em aberto nos itens 1 a 7, em 2026-11-21. O que foi aceito está registrado como
decisão em D10 e D11.

## Dúvidas

Das de maior risco para as de menor.

- D1. Templates pediam os bundles `global`, `painel` e `draft`, que não existiam, e as páginas
  deles terminavam em erro. Decisão (2026-11-21): remover. O painel do SAPL foi inteiramente
  substituído pelo `cmj/painelset`; saíram os templates, as views e rotas de `sapl/painel`, a tela
  `sessao/<pk>/painel` e `arq/draft_construct.html` (commit `068b45732`). Resolvida.
- D2. `src/__apps/painel` não era entrada. Decisão (2026-11-21): apagar, junto com D1. Resolvida.
- D3. O mixin global registrava três listeners do `EventBus` por componente e nunca os removia.
  Decisão (2026-11-21): remover em `beforeDestroy`, no próprio mixin, com teste. Chega à produção
  no próximo rebuild. Resolvida.
- D4. Nenhum código abria os WebSockets declarados. Decisão (2026-11-21): remover todo o WebSocket
  do v2018, porque tudo o que usa WebSocket já foi para o v6. Saíram o `VueNativeSock`, o
  `WebSocketManager`, as ações de socket e os timers de `store__sync`, os métodos de WebSocket do
  mixin e a dependência `vue-native-websocket`. `fetchSync` e `data_cache` ficaram. Resolvida.
- D5. A entrada `construct` só funciona porque `libsuserauth` é carregada antes pelo `base.html`
  (V2018-EST-051). Decisão (2026-11-21): manter. A tela exige `sigad.change_documento`, então o
  usuário está sempre autenticado, e a dependência fica registrada na regra e no teste dela.
  Resolvida.
- D6. Onde entra a funcionalidade complementar permitida por V2018-EST-060: em `src/modules/<x>`
  ou em `src/__apps/<app>`. Decisão (2026-11-21): caso a caso; quem pede a funcionalidade diz onde
  ela entra. Resolvida.
- D7. `package-lock.json` ficava fora do git, e o CI e os containers instalavam versões que mudavam
  sem commit. Decisão (2026-11-21): versionar o lock dos três frontends. O comando de rebuild não
  muda: ele regenera o lock e o commita com o `dist/`. O CI passa a usar `npm ci`. Resolvida.
- D10. O dev server escuta em todas as interfaces e aceita qualquer origem (V2018-EST-013).
  Decisão (2026-11-21): manter. O compose depende do dev server acessível entre containers e pelo
  navegador, e ele só existe no ambiente de desenvolvimento. Resolvida.
- D11. Dependências do v2018. Decisão (2026-11-21): (a) os pacotes do bundle com atualização dentro
  da faixa do `package.json` foram atualizados (`axios`, `js-yaml`, `markdown-it` e `tinymce`);
  (b) entrou a idade mínima de publicação (V2018-EST-016); (c) ficam aceitos até a migração para o
  v8 os avisos do `npm audit` na cadeia de build (Vue CLI 5, webpack e loaders), que não vai para o
  navegador, e o uso de Vue 2, Bootstrap 4 e BootstrapVue, que não têm mais manutenção. Atenção ao
  rebuild: apagar o lock e rodar `npm install` não atualiza o que já está em `node_modules`; para
  renovar as versões é preciso `npm update`. Resolvida.

## Fora do escopo

- O que cada módulo faz e as regras de negócio: `src/modules/loa`, `src/modules/pntp`,
  `src/__apps/loa`, `src/__apps/compilacao`, `src/__construct`. As telas da LOA têm specs em
  `docs/specs/loa/`.
- Varredura de segurança do código dos módulos, inclusive os outros usos de `v-html`
  (`fora do recorte`: `_frontend/v2018/src/modules/pntp/PntpListItem.vue:1` e mais sete arquivos).
- O SCSS e os temas de `src/__globals/2018`.
- O backend da API.
- O processo de rebuild e de deploy.
