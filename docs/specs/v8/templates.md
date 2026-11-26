# V8: templates em camadas

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `6b527f42a`)
Código principal: `_templates/v8/base_v8.html`, `_templates/v8/v8/layouts/`, `_templates/v8/v8/shell/`,
`_templates/v8/v8/paginas/zona.html`, `cmj/v8/views.py`, `cmj/v8/urls.py`,
`cmj/v8/services/s_global.py`, `_frontend/v8/src/css/temas/oficial/shell.css`
Testes: `cmj/v8/tests/test_templates.py`

Os templates do v8 formam três níveis de herança. A base só tem a infraestrutura da página. Os
layouts definem a estrutura visual e a expõem em blocks. As páginas escolhem um layout e preenchem
os blocks de conteúdo. A ordem das regiões é fixada uma vez, no nível de cima, e os níveis de baixo
só trocam o conteúdo de cada região (padrão Template Method).

```text
base_v8.html                     nível 1: infraestrutura
├─ v8/layouts/minimal.html       nível 2
└─ v8/layouts/_shell.html        nível 2, abstrato: regiões em blocks, ordem fixa
   ├─ v8/layouts/landing.html
   ├─ v8/layouts/app_topbar.html
   └─ v8/layouts/app_sidebar.html
      └─ páginas                 nível 3
```

## Escopo

- App: `cmj/v8`. Não há serviço novo: a única decisão em Python é o layout de cada zona SPA, em
  `cmj/v8/services/s_global.py`.
- Templates: `_templates/v8/base_v8.html`, `_templates/v8/v8/layouts/`, `_templates/v8/v8/shell/` e
  o `extends` das páginas existentes.
- CSS e JavaScript do shell: `_frontend/v8/src/css/temas/oficial/shell.css`,
  `_frontend/v8/src/css/temas/oficial/tokens.css`, `_frontend/v8/src/core/shell.js` e
  `_frontend/v8/src/core/boot.js`.
- Pontos de entrada: as páginas que já existiam (`/v8/`, a demonstração, a zona `demo-spa`, o 403 e
  o 404) e as páginas de demonstração dos layouts, em `/v8/demo/layouts/<nome>/`, cujo conteúdo
  está em `demo.md`.
- Legado tocado: nenhum. Nada fora de `cmj/v8`, `_templates/v8`, `_frontend/v8` e `docs/` muda.

Regras de outras specs que mudaram com esta (D9):

| Spec | Regras | Mudança |
| --- | --- | --- |
| `arquitetura.md` | V8-ARQ-020, V8-ARQ-021 | Retiradas: os blocks da base e a lista de layouts passam a ser desta spec |
| `arquitetura.md` | V8-ARQ-010, 011, 012, 022 | Mesmo comportamento, citando os layouts novos |
| `shell.md` | V8-SHELL-020, 023, 030 a 032 | Mesmo comportamento, com a evidência nos blocks de `_shell.html` e de `app_sidebar.html` |
| `shell.md` | V8-SHELL-033 | Sem JavaScript, quem mantém o menu visível é o CSS, com `@media (scripting: none)`, e não mais um `<style>` no template |
| `shell.md` | V8-SHELL-034 e 035, novas | Menu no cabeçalho: em tela estreita o botão o abre num drawer, e o grupo aberto fecha ao clicar fora ou com ESC |
| `demo.md` | V8-DEMO-040 e 041, novas | Páginas de demonstração dos quatro layouts |
| `demo.md` | V8-DEMO-010 e 020 | Citam `app_sidebar` no lugar de `admin` e de `spa` |

## Regras

### Camadas

- V8-TPL-001 [implementado] A herança tem um sentido só: página, layout concreto, `_shell.html`
  (quando o layout o usa) e `base_v8.html`. Página não estende página, e layout concreto não estende
  layout concreto. Evidência: `_templates/v8/v8/layouts/_shell.html:1`,
  `_templates/v8/v8/layouts/landing.html:1`, `_templates/v8/v8/paginas/zona.html:1`.
- V8-TPL-002 [implementado] Há quatro layouts concretos, em `v8/layouts/`: `landing.html`,
  `app_topbar.html`, `app_sidebar.html` e `minimal.html`. Os três primeiros estendem
  `v8/layouts/_shell.html`, e `minimal.html` estende `base_v8.html`. Evidência:
  `_templates/v8/v8/layouts/landing.html:1`, `_templates/v8/v8/layouts/app_topbar.html:1`,
  `_templates/v8/v8/layouts/app_sidebar.html:1`, `_templates/v8/v8/layouts/minimal.html:1`.
- V8-TPL-003 [implementado] Layout cujo nome de arquivo começa com `_` é abstrato: nenhuma página o
  estende. Nenhuma view renderiza direto um arquivo de `v8/layouts/` nem `base_v8.html`. Evidência:
  `_templates/v8/v8/layouts/_shell.html:3`, `cmj/v8/views.py:201`.

### Nível 1: base

- V8-TPL-010 [implementado] `base_v8.html` só tem o esqueleto do documento: `<!DOCTYPE html>`,
  `<html>`, `<head>` e `<body>`. Renderizada sozinha, o `<body>` contém apenas o elemento vazio
  `#cmj-v8-app`: não há cabeçalho, navegação, `<main>`, rodapé nem texto. Evidência:
  `_templates/v8/base_v8.html:23`.
- V8-TPL-011 [implementado] Os blocks da base são exatamente `html_attrs`, `title`, `meta`,
  `page_data`, `assets`, `body_class`, `layout` e `scripts`. Evidência:
  `_templates/v8/base_v8.html:3`, `_templates/v8/base_v8.html:24`.
- V8-TPL-012 [implementado] Ficam fora de qualquer block, e por isso chegam a toda página, o que a
  página precisa para funcionar: `charset`, `viewport`, favicon, `#v8-global`, `#v8-messages`, o
  cliente de HMR e o entry `main.js` do app `v8`, e `#cmj-v8-app`. Um template que sobrescreve todos
  os blocks com vazio ainda sai com todos eles. Evidência: `_templates/v8/base_v8.html:16`,
  `_templates/v8/base_v8.html:20`, `_templates/v8/base_v8.html:25`.
- V8-TPL-013 [implementado] A base emite em `<html>` só `lang`, `data-tema` (sempre, com um tema do
  registro de `temas.md`) e, havendo o cookie, `data-modo`. Qualquer outro atributo de `<html>`
  vem de um layout, pelo block `html_attrs`. Evidência: `_templates/v8/base_v8.html:3`.
- V8-TPL-014 [implementado] O padrão do block `title` é `<v8.titulo> · PortalCMJ`, ou só `PortalCMJ`
  quando a view não informa título. Os layouts não repetem essa regra. Evidência:
  `_templates/v8/base_v8.html:8`.
- V8-TPL-015 [implementado] `meta` nasce vazio e recebe descrição, `robots`, URL canônica e Open
  Graph da página. `assets`, no `<head>`, e `scripts`, no fim do `<body>`, nascem vazios e recebem
  só entradas extras do Vite e `json_script`. Evidência: `_templates/v8/base_v8.html:9`,
  `_templates/v8/base_v8.html:21`, `_templates/v8/base_v8.html:26`.
- V8-TPL-016 [implementado] A base não usa `{% include %}`, `{% cache %}`, `v8_menu` nem
  `v8_usuario`. Do contexto, lê apenas `v8.titulo`; tema e modo vêm da tag `v8_preferencias`.
  Evidência: `_templates/v8/base_v8.html:2`.

### Nível 2: shell abstrato

- V8-TPL-020 [implementado] `_shell.html` preenche o block `layout` com as regiões da página, cada
  uma num block, nesta ordem: `sprite`, `skiplink`, `header` (com `header_start`, `brand`,
  `header_nav`, `header_actions` e `user`), `aside`, o `<main>` (com `breadcrumbs`, `hero`,
  `messages` e `content`) e `footer`. O block `layout_name`, sem conteúdo padrão, recebe o nome do
  layout (V8-TPL-024). Evidência: `_templates/v8/v8/layouts/_shell.html:4`.
- V8-TPL-021 [implementado] Têm conteúdo padrão em `_shell.html`, escrito uma única vez: o sprite de
  ícones, o link "Ir para o conteúdo", a marca, o botão de modo e o de voltar ao portal antigo
  (em `header_actions`; o segundo, só com a troca de portal ligada, `portal.md`), a área do
  usuário, a trilha e as mensagens. Nascem vazios `header_start`, `header_nav`, `aside`, `hero`,
  `content` e `footer`. Evidência: `_templates/v8/v8/layouts/_shell.html:11`,
  `_templates/v8/v8/layouts/_shell.html:16`, `_templates/v8/v8/layouts/_shell.html:22`.
- V8-TPL-022 [implementado] Os layouts que estendem `_shell.html` não redefinem o block `layout`: só
  sobrescrevem blocks de região. A ordem das regiões é a mesma nos três. Evidência:
  `_templates/v8/v8/layouts/app_sidebar.html:12`, `_templates/v8/v8/layouts/app_topbar.html:9`,
  `_templates/v8/v8/layouts/landing.html:13`.
- V8-TPL-023 [implementado] Toda página de layout com shell tem um único `<main id="conteudo">`, com
  as docas `[data-v8-doca="left"]` e `[data-v8-doca="right"]` ao lado dele. Evidência:
  `_templates/v8/v8/layouts/_shell.html:42`.
- V8-TPL-024 [implementado] O elemento raiz de cada layout informa o nome dele em `data-v8-layout`,
  com um dos valores `landing`, `app_topbar`, `app_sidebar` ou `minimal`. O CSS e o JavaScript
  distinguem os layouts só por esse atributo. Evidência: `_templates/v8/v8/layouts/_shell.html:7`,
  `_templates/v8/v8/layouts/minimal.html:4`.

### Layouts concretos

- V8-TPL-030 [implementado] `app_sidebar.html` é o layout operacional: preenche `aside` com a barra
  lateral esquerda e o menu, `header_start` com o botão da sidebar e `html_attrs` com
  `data-sidebar`. A área de trabalho ocupa toda a largura que sobra. Evidência:
  `_templates/v8/v8/layouts/app_sidebar.html:4`, `_templates/v8/v8/layouts/app_sidebar.html:8`,
  `_templates/v8/v8/layouts/app_sidebar.html:13`.
- V8-TPL-031 [implementado] `app_topbar.html` é o layout de navegação superior: preenche
  `header_nav` com o menu na horizontal e `header_start` com o botão que abre o menu em tela
  estreita, e deixa `aside` vazio. O conteúdo fica centralizado, com largura máxima dada por um
  token de `tokens.css`. Não emite `data-sidebar`. Evidência:
  `_templates/v8/v8/layouts/app_topbar.html:10`, `_frontend/v8/src/css/temas/oficial/shell.css:374`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:46`.
- V8-TPL-032 [implementado] `landing.html` é o layout de capa: preenche `header_nav` e
  `header_start` como o `app_topbar`, e `footer` com a marca e uma linha de texto neutro, mais os
  sub-blocks `footer_nav` e `footer_info`, que nascem vazios. O `hero` ocupa a largura inteira da
  página, antes do conteúdo, e nasce vazio, para a página preencher. Não tem `aside` nem trilha, e
  não traz dado institucional. Evidência: `_templates/v8/v8/layouts/landing.html:10`,
  `_templates/v8/v8/layouts/landing.html:14`, `_frontend/v8/src/css/temas/oficial/shell.css:385`.
- V8-TPL-033 [implementado] `minimal.html` não tem cabeçalho, navegação, `aside`, rodapé nem docas:
  só o `<main id="conteudo">`, com os blocks `messages` e `content`. Evidência:
  `_templates/v8/v8/layouts/minimal.html:4`.
- V8-TPL-034 [implementado] Os quatro layouts oferecem os blocks `content` e `messages`. Um template
  que estende qualquer um deles e preenche só `content` renderiza sem erro tendo no contexto apenas
  o que os context processors fornecem, e sai com `#v8-global`, `#v8-messages` e `#cmj-v8-app`.
  Evidência: `_templates/v8/v8/layouts/_shell.html:63`, `_templates/v8/v8/layouts/minimal.html:6`.

### Includes

- V8-TPL-040 [implementado] Em layout e em página, todo `{% include %}` fica dentro de um block, de
  modo que o nível de baixo possa trocá-lo. Evidência: `_templates/v8/v8/layouts/_shell.html:5`,
  `_templates/v8/v8/layouts/_shell.html:62`.
- V8-TPL-041 [implementado] As parciais do shell, em `v8/shell/`, são três: o sprite de ícones, o
  menu e as mensagens em `<noscript>`. O menu ocupa dois arquivos: `menu.html`, com o `{% cache %}`,
  e `menu_itens.html`, com a recursão dos itens. Marca, botão de modo, área do usuário e trilha não
  são parciais: ficam nos blocks de `_shell.html`. Evidência:
  `_templates/v8/v8/shell/icones.html:1`, `_templates/v8/v8/shell/menu.html:5`,
  `_templates/v8/v8/shell/menu_itens.html:6`, `_templates/v8/v8/shell/mensagens.html:4`.
- V8-TPL-042 [implementado] A barra lateral de `app_sidebar` e o menu horizontal de `app_topbar` e
  de `landing` incluem a mesma parcial de menu e usam a mesma entrada de cache. A diferença entre
  eles é só de CSS. Evidência: `_templates/v8/v8/layouts/app_sidebar.html:14`,
  `_templates/v8/v8/layouts/app_topbar.html:10`, `_templates/v8/v8/layouts/landing.html:10`.

### Nível 3: páginas

- V8-TPL-050 [implementado] Toda página fica fora de `v8/layouts/` e de `v8/shell/` e estende um dos
  quatro layouts concretos. Evidência: `_templates/v8/v8/demo/clientes.html:1`,
  `_templates/v8/v8/erros/404.html:1`.
- V8-TPL-051 [implementado] Página não sobrescreve `layout`, `html_attrs` nem `layout_name`. Pode
  sobrescrever `title`, `meta`, `page_data`, `assets`, `scripts`, `body_class` e os blocks de região
  do layout que escolheu. Evidência: `_templates/v8/v8/paginas/inicio.html:2`.
- V8-TPL-052 [implementado] A zona SPA é uma página, `v8/paginas/zona.html`, que põe o elemento
  `[data-vue-zone]` no block `content`. O layout dela vem do registro de zonas, e o padrão é
  `app_sidebar`. Evidência: `_templates/v8/v8/paginas/zona.html:1`,
  `cmj/v8/services/s_global.py:103`, `cmj/v8/views.py:208`.
- V8-TPL-053 [implementado] `/v8/` usa `landing`, as páginas da demonstração usam `app_sidebar`, e o
  403 e o 404 do v8 usam `minimal`. Evidência: `_templates/v8/v8/paginas/inicio.html:1`,
  `_templates/v8/v8/demo/clientes.html:1`, `_templates/v8/v8/erros/403.html:1`.
- V8-TPL-054 [implementado] Os fragmentos de `v8/partials/` não estendem nada e não entram na
  herança. Evidência: `_templates/v8/v8/partials/demo/cliente_historico.html:1`.

## Requisitos de segurança

- V8-TPL-060 [implementado] O layout de uma página nunca vem da requisição: nem da query string, nem
  do caminho, nem de cabeçalho, nem de cookie. As páginas têm o nome do layout escrito no `extends`.
  O layout de uma zona vem só do registro de zonas, e um nome fora da lista dos quatro impede o
  projeto de subir. Itens da varredura: 3 e 4. Evidência: `cmj/v8/services/s_global.py:105`,
  `cmj/v8/views.py:208`, `cmj/v8/urls.py:75`.
- V8-TPL-061 [implementado] `#v8-global`, `#v8-messages` e o token CSRF nunca ficam dentro de `{%
  cache %}` nem dentro de um block que layout ou página possa sobrescrever. Item da varredura: 5.
  Evidência: `_templates/v8/base_v8.html:16`, `_templates/v8/v8/shell/menu.html:5`.
- V8-TPL-062 [implementado] O HTML do menu em cache é o mesmo em `app_sidebar`, `app_topbar` e
  `landing` e não contém nome, avatar, token, mensagem nem o nome do layout. Com cache real, dois
  usuários de permissões diferentes recebem menus diferentes nos três layouts. Item da varredura: 5.
  Evidência: `_templates/v8/v8/shell/menu.html:5`.
- V8-TPL-063 [implementado] Os blocks `meta`, `assets` e `scripts` não abrem exceção ao V8-ARQ-062:
  nenhum template do v8 escreve `<script`, `|safe`, `autoescape` nem atributo `on*`. A base não
  monta URL canônica nem `og:url` a partir do cabeçalho `Host`. Item da varredura: 4. Evidência:
  `_templates/v8/base_v8.html:9`.
- V8-TPL-064 [implementado] As páginas de demonstração dos layouts exigem superusuário, aceitam só
  `GET` e `HEAD`, mostram só texto fixo e não disparam PDF, IA, OCR nem task. Itens da varredura: 1
  e 7. Evidência: `cmj/v8/views.py:297`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-22, por leitura do código. A capacidade não
alcança código legado: mexe em templates, CSS e JavaScript do v8 e no app `cmj/v8`.

## Dúvidas

- D1. Landing, `app_topbar` e `app_sidebar` repetem cabeçalho, trilha, mensagens, `<main>` e docas.
  Opções: um layout abstrato comum, com as regiões em blocks; os quatro layouts estendendo a base
  direto, com as partes comuns em parciais incluídas dentro de blocks; ou um abstrato só para os
  dois `app_*`. Decisão (2026-11-22): layout abstrato comum, `v8/layouts/_shell.html`. `minimal`
  estende a base direto.
- D2. Onde ficam o Vite e os JSON globais. Recomendação: fixos, fora de block, com `assets` e
  `scripts` vazios para os extras (V8-TPL-012 e 015). Nenhuma página consegue tirar o `main.js` ou
  o `#v8-global` por engano. Alternativa: dentro de `assets`, e quem sobrescreve usa
  `{{ block.super }}`, o que dá mais liberdade e permite quebrar a página. Decisão (2026-11-22):
  fixos, fora de block.
- D3. Hoje a base emite `data-sidebar` em toda página, inclusive no 404. Recomendação: só
  `app_sidebar` emite, pelo block `html_attrs` (V8-TPL-013 e 030), porque a sidebar é assunto de um
  layout. Custo: o block `html_attrs` existe na base só para isso, e V8-SHELL-030 e 052 passam a
  valer só nesse layout. Alternativa: manter na base. Decisão (2026-11-22): só `app_sidebar`
  emite, pelo block `html_attrs`.
- D4. Layout da zona SPA. Recomendação: cada zona declara o layout em `s_global.ZONAS`, com padrão
  `app_sidebar`, e `v8/paginas/zona.html` estende o layout declarado (V8-TPL-052 e 060). É o único
  `extends` com variável do v8. Alternativa: zona sempre em `app_sidebar`, com `extends` literal, e
  o layout por zona fica para quando uma zona pedir. Decisão (2026-11-22): declarado por zona,
  com padrão `app_sidebar`.
- D5. Qual layout cada página usa, e como conferir os quatro. Recomendação: `/v8/` na `landing`,
  demonstração e zona em `app_sidebar`, erros em `minimal` (V8-TPL-053), mais quatro páginas novas
  em `/v8/demo/layouts/<nome>/`, para superusuário, cada uma num layout e com as regiões
  identificadas (V8-TPL-064, com as regras de conteúdo em `demo.md`). Sem elas não existe página no
  `app_topbar`. Alternativas: mover uma página existente para o `app_topbar`, ou deixar `/v8/` em
  `app_sidebar`. Decisão (2026-11-22): o mapa recomendado, mais as quatro páginas de demonstração.
- D6. Nomes antigos. Recomendação: apagar `admin.html`, `bare.html` e `spa.html` sem deixar alias,
  porque o v8 só tem a demonstração e nenhum código de fora os cita. Alternativa: manter os três
  como templates de uma linha que estendem os novos. Decisão (2026-11-22): apagar sem alias.
- D7. Menu horizontal do `app_topbar` e do cabeçalho da `landing`. Recomendação: a mesma árvore de
  `s_menu.py` e o mesmo HTML da sidebar (V8-TPL-042), com os grupos em `<details>`, que abrem sem
  JavaScript. Em tela estreita o menu some do cabeçalho e o botão de `header_start` o abre num
  drawer, como a sidebar faz hoje. A `landing` mostra o mesmo menu. Alternativas: um segundo menu,
  próprio da capa, ou a `landing` sem menu. Decisão (2026-11-22): o mesmo menu nos três layouts.
- D8. Conteúdo padrão do `hero` e do `footer` da `landing`. Recomendação: o layout traz só a
  estrutura e os sub-blocks, com a marca e um texto neutro no rodapé. Endereço, telefones, redes e
  demais dados institucionais ficam para quando existir a capa real. Alternativa: já trazer os dados
  institucionais do portal. Decisão (2026-11-22): só estrutura, com texto neutro.
- D9. Como registrar as mudanças nas outras specs. Recomendação: V8-ARQ-020 e 021 recebem
  `[retirada]`, substituídas por V8-TPL-011 e 002. As demais da tabela do Escopo mantêm o ID e têm o
  texto e a evidência atualizados, porque o comportamento verificável é o mesmo e só o nome do
  layout muda. Alternativa: retirar todas e reescrevê-las com IDs novos. Decisão (2026-11-22):
  retirar as duas e atualizar as demais no lugar.

## Fora do escopo

- Conteúdo e identidade visual da capa: banners, notícias, busca, dados institucionais.
- Itens de menu para telas reais e um menu próprio para o público.
- Telas reais de login e de cadastro no layout `minimal`.
- Migrar páginas do v6 ou do v2018 para os layouts novos.
- Rebuild de `dist/`.
