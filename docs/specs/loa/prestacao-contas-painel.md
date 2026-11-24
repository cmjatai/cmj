# LOA: painel de prestação de contas (v2018)

Status: observado
Última verificação: 2026-11-23 (sobre o `master` `edd6cae51`, depois da revisão da API em `docs/specs/api/`)
Código principal: `_frontend/v2018/src/modules/loa/pcl/` (o layout `PrestacaoContaLoaLayout`, os
filtros, os dois cartões, as abas, o dashboard e os helpers),
`_frontend/v2018/src/components/selects/ModelSelect.vue`,
`_frontend/v2018/src/resources/index.js`, `_frontend/v2018/src/mixins.js`, `cmj/api/forms.py`,
`cmj/api/loa/views/`, `cmj/api/loa/serializers/__init__.py`
Testes: `cmj/loa/tests/test_visibilidade_api.py`,
`_frontend/v2018/tests/apps/loa/pcl-totalizacao.spec.js`,
`_frontend/v2018/tests/apps/loa/pcl-filtros.spec.js`,
`_frontend/v2018/tests/apps/loa/pcl-dashboard.spec.js`,
`_frontend/v2018/tests/apps/loa/pcl-lista.spec.js`,
`_frontend/v2018/tests/apps/loa/pcl-falhas.spec.js`

O painel que o v2018 monta na URL `/loa/<pk>/prestacaoconta`: `PrestacaoContaLoaLayout` e todos os
componentes que ele usa, do carregamento ao último clique, e a API REST que ele consome. O lado
Django da mesma URL (rota, reCAPTCHA e relatório para impressão) está em
[prestacao-contas-tela.md](./prestacao-contas-tela.md) (`LOA-PCT`).

Todas as regras são `[observado]`: descrevem o que o código faz hoje e nenhuma foi confirmada como
regra de negócio. O JavaScript foi lido, não executado: não havia navegador nem dev server. As
regras da seção "API consumida" marcadas com "(executado)" foram conferidas em 2026-11-21 no banco
de desenvolvimento, como anônimo, com `django.test.Client` nas rotas reais, só com `GET` e a sessão
do banco em somente leitura. Em 2026-11-23, depois da revisão da API, as requisições do painel
foram repetidas da mesma forma (todas responderam 200), as medições de custo refeitas, e a
visibilidade de LOA não publicada conferida num teste descartável no banco de testes.

Não foi executado:

- O painel num navegador, por mim: não havia navegador. Os componentes alterados em 2026-11-23
  (totalização, dashboard, lista e cartões) são exercitados pelos testes do Vitest, e o usuário
  conferiu a totalização e o dashboard na tela; o restante é conclusão de leitura.
- Casos com LOA não publicada na base de desenvolvimento, onde todas estão publicadas. Só a lista e
  o detalhe de `loa/loa`, a lista de ofícios e o total dos ajustes foram conferidos no banco de
  testes.
- O download dos arquivos de prestação de contas.

## Escopo

- `PrestacaoContaLoaLayout.vue`: estado, carga inicial, filtros, busca, cache, paginação, URL.
- Os componentes filhos: `PclFiltros`, `PclDetalheEmenda`, `PclDetalheAjuste`, as cinco abas
  (`tabs/`), `PclTotalizacao`, `PclDashboard` e `pcl-helpers.js`.
- O que o painel usa da base do v2018: `Resources.Utils.fetch`, `ModelSelect`, `fetchSync` e
  `removeAside`.
- Os endpoints da API chamados pelo painel: quem acessa, o que devolvem e o que custam.

## Regras

### Montagem e carga inicial

- LOA-PCL-001 [observado] O painel é o componente da rota `prestacaoconta_route` e recebe o `pk` da
  URL em `$route.params.pkloa`. Evidência: `_frontend/v2018/src/routers.js:22-26`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:104`.
- LOA-PCL-002 [observado] Ao montar, o painel restaura o modo de visualização (LOA-PCL-014), remove
  o `<aside>` da página (`removeAside`, que também tira o id `wrapper` e põe a classe `appvue` no
  `<main>`) e faz a carga inicial, com duas requisições em paralelo: a LOA da rota, só com `id` e
  `ano`, e o resumo da prestação de contas dela, de onde vem a lista de exercícios (LOA-PCL-102).
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:578-596`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:622-626`,
  `_frontend/v2018/src/mixins.js:158-173`.
- LOA-PCL-003 [observado] O conteúdo do painel só é exibido depois que a LOA da rota chega: ele
  depende de `loa.ano`. Se a requisição da LOA falhar, a tela mostra o aviso de LOA-PCL-104; a dos
  exercícios, se falhar, deixa a lista de exercícios vazia. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:3`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:589-597`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:618-620`.
- LOA-PCL-004 [observado] Com as respostas, a LOA da rota vira o exercício principal e o único
  selecionado. Se a URL traz `loas=<ids>`, entram na seleção os ids que estão na lista de exercícios
  e são diferentes do principal. Em seguida o painel pede as opções dos filtros para a seleção
  (LOA-PCL-106). Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:596-611`.
- LOA-PCL-005 [observado] Com as opções recebidas, o painel lê os filtros da URL (LOA-PCL-016),
  marca-se pronto, reescreve a query string (LOA-PCL-015) e faz a primeira busca. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:611-617`.
- LOA-PCL-006 [observado] Quando a URL traz filtros, a leitura deles altera `filters_value` antes de
  o painel se marcar pronto, mas o observador dos filtros roda depois, já com o painel pronto. O
  resultado é uma segunda busca, cujas respostas substituem as da primeira (LOA-PCL-099). Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:178-186`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:612-616`.
- LOA-PCL-007 [retirada] Substituída por LOA-PCL-102 e LOA-PCC-005.

### Estrutura da tela

- LOA-PCL-008 [observado] A tela tem, de cima para baixo: o bloco de filtros; a totalização (só no
  modo lista e quando o resumo chega com itens); e, conforme o modo, o dashboard ou a lista de
  cartões. Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:4-66`.
- LOA-PCL-009 [observado] A lista de cartões aparece no modo lista quando há itens ou uma busca em
  andamento. Cada item vira um cartão de emenda (`__label__` igual a `loa_emendaloa`) ou de ajuste.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:48-69`.
- LOA-PCL-010 [observado] "Nenhum resultado encontrado para os filtros selecionados." aparece só no
  modo lista, com o painel pronto, sem itens, sem busca em andamento e sem falha (LOA-PCL-104). No
  modo dashboard sem itens, a área de conteúdo fica vazia, sem mensagem. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:38-39`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:71-73`.
- LOA-PCL-011 [observado] Os filtros ficam desabilitados enquanto o painel não está pronto ou a
  primeira página da busca corrente não chegou. Nesse intervalo o painel chama
  `window.loadingCMJ('Atualizando filtros...')`, e `window.unloadingCMJ` ao reabilitar. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:6`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:265-272`.

### Estado, URL e armazenamento local

- LOA-PCL-012 [observado] Os filtros são sete: `unidade`, `entidade`, `parlamentares`, `situacao`,
  `emendas_tipos`, `ajustes` e `search`. O estado inicial é sem unidade, entidade e parlamentar,
  listas vazias, `ajustes` igual a `'False'` e busca vazia. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:113-131`.
- LOA-PCL-013 [observado] Qualquer mudança em `filters_value`, com o painel pronto, volta para a
  página 1, reescreve a query string e refaz a busca inteira. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:178-186`.
- LOA-PCL-014 [observado] O modo de visualização (`list` ou `dashboard`) vem de `view` na URL; na
  falta, de `portalcmj_pcl_view_mode` no `localStorage`; na falta, `list`. Trocar o modo grava no
  `localStorage` e reescreve a query string, sem refazer a busca. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:226-246`.
- LOA-PCL-015 [observado] A query string é reescrita com `router.replace`, sem criar entrada no
  histórico. Leva `view`, cada filtro não nulo (lista vira valores separados por vírgula, objeto
  vira o `id`) e `loas` com os exercícios extras. Unidade, entidade e parlamentar nulos ficam fora;
  listas vazias e a busca vazia vão como parâmetro vazio. O link resultante reproduz a tela.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:297-322`.
- LOA-PCL-016 [observado] Na leitura da URL: `situacao` e `emendas_tipos` são separados por
  vírgula; `ajustes` e `search` entram como vieram; `parlamentares` só é aceito se o id estiver
  entre os parlamentares da LOA principal; `unidade` e `entidade` esperam o seletor carregar e
  escolhem a opção com o id. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:523-553`.
- LOA-PCL-017 [retirada] Substituída por LOA-PCL-103.
- LOA-PCL-103 [implementado] Para `unidade` e `entidade` vindos da URL, o painel espera a opção do
  id pedido aparecer no seletor, testando a cada 100 ms, e então aplica o filtro. Se a opção não
  aparecer em 10 segundos, desiste: o filtro da URL é descartado e a tela segue sem ele. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:512-522`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:537-547`.
- LOA-PCL-104 [implementado] Falha numa requisição da carga inicial ou da busca (resumo, dashboard
  ou página de cartões) é avisada na tela: "Não foi possível carregar os dados da prestação de
  contas.", com o botão "Tentar novamente", que refaz a carga ou a busca. O aviso some quando a nova
  tentativa dá certo, e "Nenhum resultado encontrado" fica só para quando não há resultado. A
  resposta 404 das consultas, que é a de LOA sem prestação de contas (LOA-PCL-102), não é tratada
  como falha. Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:25-32`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:75-82`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:290-296`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:618-620`.
- LOA-PCL-105 [implementado] Falha na requisição do conteúdo de uma aba marca só aquela aba, que
  mostra "Não foi possível carregar." com o link "Tentar novamente" no lugar de "Carregando..."; as
  outras abas do cartão carregam normalmente. Tentar de novo refaz a carga das abas do cartão.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:379-390`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:251-262`,
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabPrestacao.vue:3-6`.
- LOA-PCL-106 [implementado] As opções dos seletores "Parlamentares", "Entidades" e "Unidade
  Orçamentária" vêm do backend (`prestacaoconta_opcoes`, LOA-PCC-090), para os exercícios
  selecionados: são pedidas na carga inicial, antes da leitura dos filtros da URL, e de novo a cada
  troca de exercício. O filtro cujo valor deixou de existir entre as opções, por um exercício
  desmarcado, é descartado, e a busca é refeita sem ele. Os seletores não usam mais o cache comum do
  v2018 nem as rotas `loa/entidade` e `loa/unidadeorcamentaria`. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:158-176`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:189-224`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:487-510`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:59-78`.
- LOA-PCL-018 [observado] O tamanho da página da lista vem de `portalcmj_page_size` no
  `localStorage`, com padrão 10, e é gravado a cada troca. A chave não é exclusiva deste painel.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:147`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:392-397`.

### Bloco de filtros

- LOA-PCL-019 [observado] "EXERCÍCIO" mostra um botão por LOA da lista (ano). Clicar marca ou
  desmarca o exercício, exceto o principal, que fica travado. Os botões não respondem enquanto os
  filtros estão desabilitados. Evidência: `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:8-28`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:342-353`.
- LOA-PCL-020 [retirada] Substituída por LOA-PCL-093.
- LOA-PCL-093 [implementado] Cada botão de exercício tem um ícone "Tornar este exercício o
  principal", que é um link para a prestação de contas daquele exercício
  (`/loa/<id>/prestacaoconta`). O clique no ícone não marca nem desmarca o exercício. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:20-26`.
- LOA-PCL-021 [observado] "Pesquisa" é aplicada ao sair do campo ou ao teclar Enter; o botão da lupa
  só tira o foco do campo. Evidência: `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:33-48`.
- LOA-PCL-022 [observado] "Parlamentares" lista as opções recebidas do backend (LOA-PCL-106), em
  ordem alfabética, com uma opção vazia quando há mais de um. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:158-163`.
- LOA-PCL-023 [retirada] Substituída por LOA-PCL-106.
- LOA-PCL-024 [retirada] Substituída por LOA-PCL-106 e LOA-PCC-090.
- LOA-PCL-025 [observado] "Unidade Orçamentária" fica desabilitada com mais de um exercício
  selecionado, e a unidade escolhida é limpa quando um exercício é acrescentado. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:76`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:503-507`.
- LOA-PCL-026 [observado] "Documentos" tem três tipos de emenda (10 Impositivas da Saúde, 99
  Impositivas de Áreas Diversas, 0 Modificativas) e a caixa "Registros de Ajustes", que vale `True`
  ou `False`. "Situação" tem Registrado, Em Execução, Finalizado e Impedido. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:82-111`.
- LOA-PCL-027 [observado] "Limpar" volta os filtros ao estado inicial e deixa só o exercício
  principal selecionado. O modo de visualização e o tamanho da página não mudam. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:378-391`.
- LOA-PCL-028 [observado] O rodapé do bloco tem os botões de modo (lista e dashboard), o link da
  versão para impressão e, havendo itens, o texto "início–fim de total", com um indicador enquanto a
  busca carrega. O seletor de tamanho de página (10, 25, 50, 100) e os botões de página aparecem só
  no modo lista. São mostradas até cinco páginas em torno da atual. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:119-189`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:276-305`.
- LOA-PCL-029 [observado] O link de impressão é a URL atual do navegador com `print=True` e com
  `emendas_tipos` renomeado para `tipo__in`; abre em nova aba. É recalculado a cada mudança de
  filtro. Os demais parâmetros (`view`, `loas`) seguem no link e são ignorados pelo relatório
  (LOA-PCT-026). Evidência: `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:197-208`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:307-323`,
  `_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:134-139`.

### Busca

- LOA-PCL-030 [retirada] Substituída por LOA-PCC-002: o que entra na busca é decidido no backend.
- LOA-PCL-031 [retirada] Substituída por LOA-PCL-099.
- LOA-PCL-032 [retirada] Substituída por LOA-PCL-099.
- LOA-PCL-033 [retirada] Substituída por LOA-PCL-089 e LOA-PCC-001.
- LOA-PCL-034 [retirada] Substituída por LOA-PCL-098 e 099: não há mais cache de registros.
- LOA-PCL-035 [retirada] Substituída por LOA-PCL-099.
- LOA-PCL-036 [retirada] Substituída por LOA-PCC-040: a ordem da lista vem do backend.
- LOA-PCL-037 [retirada] Substituída por LOA-PCL-099.
- LOA-PCL-038 [observado] Marcar ou desmarcar um exercício pede de novo as opções dos filtros
  (LOA-PCL-106), refaz a busca inteira com os exercícios selecionados, volta para a página 1 e
  reescreve a query string. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:487-510`.
- LOA-PCL-039 [retirada] Substituída por LOA-PCL-104.

### Totais de empenhos

- LOA-PCL-040 [retirada] Substituída por LOA-PCL-089.
- LOA-PCL-041 [retirada] Substituída por LOA-PCL-089 e LOA-PCC-021.

### Atalhos de filtro nos cartões e no dashboard

- LOA-PCL-042 [observado] Clicar na foto de um parlamentar, ou no nome dele no dashboard, aplica o
  filtro de parlamentar. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:340-351`.
- LOA-PCL-043 [observado] Clicar numa unidade orçamentária aplica o filtro de unidade, exceto com
  mais de um exercício selecionado. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:323-339`.
- LOA-PCL-044 [observado] Clicar numa entidade aplica o filtro de entidade e, junto, marca os tipos
  10 e 99 e desmarca "Registros de Ajustes". Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:352-377`.
- LOA-PCL-045 [observado] Clicar numa emenda vinculada (no cartão do ajuste) ou na descrição de um
  ajuste (na aba da emenda) põe o texto na busca, limpa os tipos e desmarca "Registros de Ajustes".
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:58`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:65`.

### Cartão da emenda

- LOA-PCL-046 [observado] O cabeçalho mostra as fotos dos parlamentares (miniatura `.c128.png`), o
  título com link para o detalhe da emenda no backend em nova aba, o tipo e a fase (LOA-PCL-100). O
  título vem do backend: a epígrafe da matéria ou, sem matéria, o valor da emenda. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:9-46`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:311-324`.
- LOA-PCL-047 [observado] "Valor Original" é `str_valor`. "Valor Final" (`str_valor_computado`)
  aparece quando a emenda tem ajustes ou o valor computado é zero. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:49-67`.
- LOA-PCL-048 [observado] O corpo mostra a unidade orçamentária e o beneficiário (nome fantasia da
  entidade), ambos clicáveis, e o "Objeto Inicial" (`ementa_format`), riscado quando há ajustes e
  valor computado. Com ajustes, um aviso manda ver a aba "Ajustes Técnicos". O template também
  prevê CNES ou CPF/CNPJ da entidade, mas o painel não pede esses campos à API e eles nunca
  aparecem. Evidência: `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:74-122`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:465-467`.
- LOA-PCL-049 [observado] As abas só existem para emenda impositiva (tipo diferente de 0). A ordem é
  Prestação de Contas, Ajustes Técnicos e Empenhos, com as que têm dados na frente (LOA-PCL-101),
  seguidas de Tramitações e Documentos Acessórios quando há matéria. A primeira da ordem abre ativa.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:125-217`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:340-351`.
- LOA-PCL-050 [observado] O conteúdo das abas é buscado só quando o cartão chega a 200 px da área
  visível, uma vez por cartão, e de novo se o registro do cartão mudar: registros de prestação de
  contas, registros de ajuste, empenhos e, com matéria, documentos acessórios e tramitações, cada um
  sem paginação (`get_all`) e só quando a contagem do item diz que há dados (LOA-PCL-101).
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:284-298`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:390-476`.
- LOA-PCL-051 [retirada] Substituída por LOA-PCL-101.
- LOA-PCL-052 [retirada] Substituída por LOA-PCL-105.

### Cartão do ajuste

- LOA-PCL-053 [observado] O cabeçalho mostra as fotos dos parlamentares do registro
  (`parlamentares_valor`), o título com link para o detalhe, o tipo (Ajuste Saúde ou Ajuste Áreas
  Diversas) e a fase (LOA-PCL-100). "Valor do Ajuste" é `str_valor`, com o valor negativo entre
  parênteses; "Valor Final" aparece quando `str_valor_computado` é diferente. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:9-64`.
- LOA-PCL-054 [observado] O corpo mostra a unidade (clicável), as emendas vinculadas (o trecho de
  `__str__` antes do primeiro hífen, clicável) e a descrição. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:70-101`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:214-226`.
- LOA-PCL-055 [observado] As abas do ajuste (Prestação de Contas, quando há registros, e Empenhos)
  só aparecem se ao menos uma tiver dados, pelas contagens do item (LOA-PCL-101). O conteúdo é
  buscado sob demanda, como na emenda. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:104-137`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:211-213`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:262-291`.

### Abas

- LOA-PCL-056 [observado] Toda aba mostra "Carregando..." enquanto os dados não chegam, uma frase
  própria quando a lista vem vazia e o aviso de LOA-PCL-105 quando a requisição falha. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabAjustes.vue:3-12`.
- LOA-PCL-057 [observado] Prestação de Contas: por registro, o título do lote com link para o
  detalhe, "Encaminhado em" com a data de envio, o detalhamento (ou "Sem descrição de
  detalhamento"), os arquivos próprios do registro com link (ou "Nenhum arquivo anexado") e a
  situação (Em Análise/Execução ou Finalizada). Quando o registro se refere a um ajuste diferente
  do cartão, mostra "Relativo ao Ajuste Técnico". Os arquivos gerais do lote não aparecem no
  painel. Evidência: `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabPrestacao.vue:17-66`,
  `_frontend/v2018/src/modules/loa/pcl/utils/pcl-helpers.js:87-103`.
- LOA-PCL-058 [observado] Ajustes Técnicos: o total dos ajustes e, por ajuste, o `__str__` com link,
  a unidade, a descrição (clicável, LOA-PCL-045) e o valor. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabAjustes.vue:14-56`.
- LOA-PCL-059 [observado] Empenhos: quatro totais somados no navegador (empenhado, liquidado, pago
  bruto, anulado) e, por empenho, código, fornecedor com CPF/CNPJ, data, modalidade, histórico e
  valores. Um aviso marca o empenho ligado a mais de uma emenda ou ajuste. Clicar abre um quadro com
  os quatro valores, a tabela de `metadata.scrap.values` (dados copiados do portal de origem) e o
  histórico; a linha "Código" leva ao detalhe do empenho. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabEmpenhos.vue:14-155`,
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabEmpenhos.vue:178-209`.
- LOA-PCL-060 [observado] Tramitações: data, turno, urgência, status, unidade local e destino, o
  texto cortado em 40 palavras, encaminhamento e fim de prazo. Documentos Acessórios: link do
  arquivo, nome, tipo, data, autor e ementa cortada em 30 palavras. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabTramitacoes.vue:17-53`,
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabDocumentos.vue:14-45`.
- LOA-PCL-061 [observado] Nenhum componente do painel usa `v-html`: todo texto da API é exibido com
  escape. Evidência: `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabPrestacao.vue:30-49`.

### Rótulos

- LOA-PCL-062 [observado] Os rótulos e cores de tipo, fase e situação são fixos em
  `pcl-helpers.js`, separados do backend. Fases de emenda: 10 Proposta, 12 Proposta Liberada, 15
  Edição Contábil, 17 Liberado Contab., 20 Em Tramitação, 25 Aprov. Legislativa, 30 Aprovada, 40
  Impedimento, 50 Emenda Redefinida/Sanada, 60 Em Execução, 99 Finalizada. Fases de ajuste: 10
  Registrado, 40 Impedimento, 60 Em Execução, 90 Finalizado. Valor fora da tabela aparece como
  "Fase N" ou "Tipo N". Evidência: `_frontend/v2018/src/modules/loa/pcl/utils/pcl-helpers.js:6-72`,
  `_frontend/v2018/src/modules/loa/pcl/utils/pcl-helpers.js:105-131`.
- LOA-PCL-084 [retirada] Substituída por LOA-PCL-100.

### Totalização

- LOA-PCL-063 [retirada] Substituída por LOA-PCL-090.
- LOA-PCL-064 [retirada] Substituída por LOA-PCC-010 a 012: o valor de cada item é decidido no
  serviço.
- LOA-PCL-065 [retirada] Substituída por LOA-PCL-091.
- LOA-PCL-066 [retirada] Removida: o bloco de agrupamento por tipo, sempre oculto, e
  `permissionEdit` saíram do componente.
- LOA-PCL-089 [implementado] A cada busca o painel pede o resumo (`prestacaoconta_resumo`, LOA-PCC)
  uma vez, com os filtros da busca e os exercícios extras selecionados, e é dele que vêm a
  totalização e a execução; o painel não soma mais respostas por exercício nem por tipo de
  documento. A resposta de uma busca anterior é descartada, e falha na requisição deixa a tela sem
  totalização. Desmarcar um exercício pede o resumo de novo. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:247-296`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:33-37`.
- LOA-PCL-090 [implementado] A totalização só apresenta o resumo: quantos registros entram na conta
  e, para "Total Impositivas", "Saúde", "Áreas Diversas" e, se maior que zero, "Modificativas", o
  valor e a contagem do próprio grupo. A contagem ao lado de "Total Impositivas" é a das impositivas
  (LOA-PCC-020). Nenhuma regra de valor fica no componente. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:2-34`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:72-90`.
- LOA-PCL-091 [implementado] A linha de execução (Total Empenhado, Liquidado, Pago e Anulado, cada
  um com o percentual sobre "Total Impositivas") aparece quando algum total é maior que zero e o
  resumo diz que a execução vale para os exercícios pedidos (LOA-PCC-022). Quando não vale, aparece
  o aviso de que os totais só são computados a partir do ano inicial, que também vem do resumo.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:42-59`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:91-105`.
- LOA-PCL-092 [implementado] Abaixo dos totais, a totalização avisa quantas emendas da seleção
  contam com valor zero por terem o valor remanejado para registros de ajuste, e quantas por
  impedimento técnico, com o valor original de cada grupo (LOA-PCC-023). Quando a seleção não tem
  ajustes, o aviso diz que eles não estão na seleção. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:36-40`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclTotalizacao.vue:106-125`.

### Dashboard

- LOA-PCL-067 [retirada] Substituída por LOA-PCL-094 e 097.
- LOA-PCL-068 [retirada] Substituída por LOA-PCL-094 e LOA-PCC-030.
- LOA-PCL-069 [retirada] Substituída por LOA-PCL-095 e LOA-PCC-031.
- LOA-PCL-070 [retirada] Substituída por LOA-PCC-013.
- LOA-PCL-071 [retirada] Substituída por LOA-PCL-096, LOA-PCC-032 e 033.
- LOA-PCL-072 [observado] Os nomes de parlamentar, unidade e entidade do dashboard são atalhos de
  filtro (LOA-PCL-042 a 044). Cada seção tem "Expandir todos" e "Recolher todos". Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:10-328`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:535-611`.
- LOA-PCL-094 [implementado] O dashboard só apresenta as distribuições que vêm de
  `prestacaoconta_dashboard` (LOA-PCC-030 a 034), e não aparece enquanto elas não chegam. No topo
  repete a totalização, com o mesmo resumo. "Situação — Saúde" e "Situação — Áreas Diversas" mostram
  os grupos como vêm, com rótulo, contagem, valor e a distribuição por parlamentar; no painel ficam
  só a barra, proporcional à contagem do maior grupo, e a cor, pela posição. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:1-8`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:383-405`.
- LOA-PCL-095 [implementado] "Distribuição por Parlamentar em Áreas Diversas" mostra, por
  parlamentar, o total, as contagens de emendas e de ajustes e uma barra com um segmento por unidade
  orçamentária. A mesma unidade tem a mesma cor em todos os parlamentares; o item sem unidade
  aparece como "Sem unidade"; com mais de um exercício, o nome da unidade leva o ano. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:407-446`.
- LOA-PCL-096 [implementado] "Distribuição por Unidade Orçamentária" e "por Entidade/Beneficiário"
  mostram as dez maiores da lista recebida, ou todas quando há filtro de parlamentar, com a barra
  proporcional à maior e o detalhe por parlamentar. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:448-468`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:487-509`.
- LOA-PCL-097 [implementado] As distribuições são pedidas só com o dashboard aberto: nesse modo,
  cada busca pede `prestacaoconta_dashboard` junto com o resumo, com os mesmos filtros e exercícios;
  no modo lista, a busca só descarta as distribuições anteriores, e abrir o dashboard as pede. A
  resposta de uma busca anterior é descartada. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:263-296`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:228-234`.
- LOA-PCL-098 [implementado] Cada item de `prestacaoconta_itens` (LOA-PCC-041) chega ao cartão com
  os valores já decididos pelo backend; o painel só formata o dinheiro e põe o item no formato que
  os cartões usam, com o exercício a que pertence. Não há cache de registros no navegador.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:434-485`.
- LOA-PCL-099 [implementado] A lista é paginada pelo servidor: uma busca pede o resumo e a página em
  exibição de `prestacaoconta_itens`, com os mesmos filtros e exercícios, e o painel nunca carrega a
  LOA inteira. Trocar de página ou de tamanho de página pede só a nova página. Vale a resposta do
  pedido mais recente; a de uma busca ou de uma página anterior é descartada. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:392-432`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:557-574`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:48-49`.
- LOA-PCL-100 [implementado] O rótulo da fase mostrado nos cartões é o que vem do backend
  (LOA-PCC-042): o ajuste finalizado aparece como "Finalizado", com a cor da fase 99. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:44`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:39`,
  `_frontend/v2018/src/modules/loa/pcl/utils/pcl-helpers.js:61-72`.
- LOA-PCL-101 [implementado] As contagens que cada item traz (LOA-PCC-043) decidem quais abas têm
  dados e a ordem delas, antes de qualquer requisição, e aparecem no selo de cada aba. Aba com
  contagem zero não gera requisição. A aba Empenhos da emenda reúne os vínculos dela e os dos
  ajustes dela, sem repetir, e espera a lista de ajustes chegar antes de buscar os empenhos deles.
  Evidência: `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:340-351`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:368-389`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:422-442`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:211-213`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheAjuste.vue:241-261`.
- LOA-PCL-102 [implementado] Os botões de exercício vêm do backend: são os exercícios com prestação
  de contas para o usuário (LOA-PCC-024), do mais recente para o mais antigo. Exercício pedido na
  URL (`loas=`) que não esteja nessa lista é ignorado. Quando a LOA da rota não tem prestação de
  contas, não há botões nem itens, e a tela mostra "Nenhum resultado encontrado". Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:587-607`.
- LOA-PCL-073 [observado] O dashboard termina com um aviso fixo de que outros gráficos estão em
  desenvolvimento. `PclSaude.vue` e `PclDashboardTestChart.vue` existem na pasta e não são usados
  por nenhum componente. Evidência:
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboard.vue:329-332`,
  `_frontend/v2018/src/modules/loa/pcl/dash/PclDashboardTestChart.vue:30-37`.

### API consumida

- LOA-PCL-074 [observado] Toda requisição do painel é `GET` em `/api/<app>/<model>/`, montada por
  `Resources.Utils.fetch`, com cabeçalhos que pedem resposta sem cache. O painel não grava nada.
  Evidência: `_frontend/v2018/src/resources/index.js:6-8`,
  `_frontend/v2018/src/resources/index.js:96-105`.
- LOA-PCL-075 [observado] Os endpoints usados são: `loa/loa` (o detalhe e as quatro consultas da
  prestação de contas: resumo, dashboard, itens e opções), `loa/registroajusteloa`,
  `loa/prestacaocontaregistro` e `loa/empenhoemendaajuste` (conteúdo das abas),
  `materia/documentoacessorio` e `materia/tramitacao`. Todos respondem 200 a anônimo (executado). O
  painel não chama mais a lista de `loa/emendaloa`, os `totalize_empenhos`, `loa/entidade` nem
  `loa/unidadeorcamentaria`. Evidência: `cmj/globalrules/map_rules.py:244-259`,
  `cmj/globalrules/map_rules.py:285-288`, `sapl/rules/map_rules.py:151-160`,
  `sapl/api/permissions.py:51-57`.
- LOA-PCL-076 [observado] A lista de emendas segue a visibilidade da listagem (LOA-LST-083): anônimo
  recebe as emendas de LOA publicada, em qualquer fase. Na LOA 2027, publicada e ainda sem norma, a
  API entrega as 164 emendas das fases 12 e 15 (executado). `owner`, `metadata` e `search` não são
  entregues a quem não edita a emenda (LOA-LST-091). Evidência:
  `cmj/api/loa/views/emendaloa.py:61-67`, `cmj/api/loa/serializers/__init__.py:100-124`.
- LOA-PCL-077 [retirada] Substituída por LOA-PCL-086.
- LOA-PCL-086 [implementado] Os demais endpoints que o painel consulta seguem a mesma visibilidade
  das emendas, pela LOA a que o registro pertence (API-ACS-051): a lista de LOAs e o detalhe, os
  ofícios e registros de ajuste e os seus totais, os registros de prestação de contas e os empenhos
  vinculados. Em LOA não publicada, anônimo e conta comum não recebem nada, e o detalhe responde
  404. Evidência: `cmj/loa/services/s_visibilidade.py:69-80`,
  `cmj/api/loa/views/__init__.py:130-143`.
- LOA-PCL-078 [observado] A paginação padrão é de 10 itens, com `page_size` até 100. `get_all=true`
  desliga a paginação; para quem não tem `list_` do model, só até 2.000 itens, e acima disso a
  resposta é 400 (API-CUS-020; executado: a lista de empenhos, com 117 mil linhas, responde 400 a
  anônimo). O painel só usa `get_all` no conteúdo das abas, com filtro por registro pai
  (LOA-PCL-050, API-CUS-017), e nenhum desses pedidos chega perto do teto. Evidência:
  `sapl/api/pagination.py:9-35`.
- LOA-PCL-079 [observado] `totalize_empenhos` aplica os filtros da lista, reúne os empenhos
  distintos ligados aos itens filtrados e soma empenhado, liquidado, pago bruto e anulado.
  Evidência: `cmj/api/loa/views/emendaloa.py:369-386`,
  `cmj/api/loa/views/registroajusteloa.py:16-33`.
- LOA-PCL-080 [observado] Cada item de emenda traz valores calculados no serializer: `str_valor`,
  `str_valor_computado`, `valor_inicial`, `valor_computado`, `valor_inicial_por_parlamentar`,
  `has_ajustes`, `ementa_format`, `epigrafe_short` e as quatro somas de empenhos. O ajuste traz
  `valor` (soma das partes), `valor_por_parlamentar` (zerado quando o valor computado é zero) e as
  mesmas somas. Evidência: `cmj/api/loa/serializers/__init__.py:157-199`,
  `cmj/api/loa/serializers/__init__.py:202-254`.
- LOA-PCL-081 [observado] (executado na LOA 2026, em 2026-11-23) As rotas `loa/emendaloa` e
  `loa/registroajusteloa`, que o painel percorria e não percorre mais (LOA-PCL-099), deixaram de
  custar 13 consultas por item (LOA-PCC-080): uma página de 100 emendas faz 7 consultas, e uma de
  100 ajustes, 12. Com os parâmetros de `expand` que o painel usava, 100 ajustes fazem 201 consultas
  (0,35 s), contra 2.740 (2,1 s) antes. A página de 40 cartões da consulta nova custa de 7 a 10.
  Evidência: `cmj/api/loa/serializers/__init__.py:23-75`.
- LOA-PCL-082 [observado] No conteúdo da aba Empenhos, o empenho expandido vem com todos os campos,
  entre eles `nome`, `cpfcnpj`, `search` e `metadata` (executado; LOA-PCL-087). Evidência:
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:425-429`.
- LOA-PCL-083 [observado] A consulta de entidades por `loa` devolve as que têm emenda ou registro
  de ajuste na LOA. Evidência: `cmj/api/forms.py:36-41`.
- LOA-PCL-085 [observado] (executado, 2026-11-23) O painel não depende de campo que a API esconde
  de anônimo. As tramitações chegam sem `ip` e `user` (API-SER-028), e as emendas sem `owner`,
  `metadata` e `search`, que para anônimo também não valem como filtro nem como ordenação
  (API-FIL-022). A busca do painel usa o filtro declarado `search`, que continua valendo para todos.
  Evidência: `cmj/api/forms.py:58-60`, `cmj/api/loa/serializers/__init__.py:100-116`,
  `_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:320-322`.
- LOA-PCL-087 [acordado] Nome e documento do credor de cada empenho são dado público de
  transparência, na API e nas telas: `loa/empenho` e `loa/empenhoemendaajuste` entregam `nome`,
  `cpfcnpj` e os mesmos valores dentro de `metadata.scrap` a qualquer usuário, e a lista de
  empenhos pode ser filtrada por documento. O CNPJ sai completo; o CPF sai mascarado
  (`999.***.***-99`), máscara que o importador aplica ao documento de 14 caracteres. Aceito em
  2026-11-23: as telas públicas já mostram o mesmo dado (aba Empenhos do painel, relatório da
  prestação de contas e cartão da listagem de emendas), que vem do portal de transparência do
  município. (executado) Na base de desenvolvimento, dos 117.327 empenhos, 76.829 têm CNPJ e 40.498
  têm CPF mascarado; nenhum tem CPF completo. Um CPF completo na base, como um que chegue à
  importação sem pontuação e escape da máscara, exige rever esta regra. Evidência:
  `cmj/loa/management/commands/scrap_centi.py:560-564`, `cmj/globalrules/map_rules.py:256-257`,
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabEmpenhos.vue:51`,
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:142`.
- LOA-PCL-088 [acordado] `loa/entidade` entrega o `cpfcnpj` da entidade a qualquer usuário, como o
  relatório da prestação de contas e o cartão da listagem de emendas. Aceito em 2026-11-23 pela
  mesma razão de LOA-PCL-087. (executado) As 353 entidades da base têm CNPJ, e nenhuma das 276 com
  campos de importação traz CPF neles. Cadastrar entidade pessoa física exige rever esta regra.
  Evidência: `cmj/api/forms.py:21-34`,
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:40`,
  `_templates/v2018/loa/emendaloa_filter_cache.html:91-92`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1 a 7 de `docs/specs/README.md`, sobre o painel e os endpoints que
ele chama, revista em 2026-11-23 depois da revisão da API (`docs/specs/api/`). Não é auditoria da
API inteira.
O custo por item das rotas de emendas e de ajustes, achado na mesma varredura, foi sanado em
2026-11-23 (LOA-PCC-080).

## Dúvidas

Nenhuma dúvida em aberto (2026-11-23).

## Pendências encontradas

Código sem uso ou sem efeito, por leitura:

- `PclSaude.vue` e `PclDashboardTestChart.vue` não são importados (LOA-PCL-073).
- O cartão da emenda prevê CNES e CPF/CNPJ que o painel não pede (LOA-PCL-048).
- `dash_activated` é sempre verdadeiro: os botões de modo sempre aparecem
  (`_frontend/v2018/src/modules/loa/pcl/PrestacaoContaLoaLayout.vue:112-114`).
- `filtersDisabled` chama `loadingCMJ` e `unloadingCMJ` dentro de uma propriedade computada
  (`_frontend/v2018/src/modules/loa/pcl/PclFiltros.vue:265-272`).
- Os dois ramos de rótulo do "Valor Final" da emenda mostram o mesmo texto
  (`_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:64-65`).

## Fora do escopo

- O lado Django da URL e o relatório para impressão:
  [prestacao-contas-tela.md](./prestacao-contas-tela.md).
- A cópia do painel em `_frontend/v6/src/modules/loa/pcl/`.
- `LoaList`, `LoaDetail` e `LoaDash`, as outras rotas de `/loa/` no v2018.
- As regras de visibilidade e de campos internos da emenda na API: `listagem-emendas.md`
  (LOA-LST-083 e 091).
- A estrutura do v2018 (entradas, roteador, stores, `App`): `docs/specs/v2018/estrutura.md`.
- O `drfautoapi` (como `expand`, `include`, `exclude` e os filtros são gerados).
