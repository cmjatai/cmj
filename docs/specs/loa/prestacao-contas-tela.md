# LOA: tela de prestação de contas (rota, reCAPTCHA e versão para impressão)

Status: observado, com nove regras implementadas (LOA-PCT-007 e 063 a 070) e quatro acordadas
Última verificação: 2026-11-23 (sobre o `master` `edd6cae51`)
Código principal: `cmj/loa/views/v_loa.py` (`LoaCrud.PrestacaoContaView`), `cmj/mixins.py`
(`GoogleRecapthaViewMixin`), `cmj/search/views.py` (`InfoFilterMixin`), `cmj/api/forms.py`,
`_templates/v2018/loa/prestacaoconta_detail.html`, `_templates/v2018/loa/prestacaoconta_print.html`,
`_templates/v2018/loa/prestacaocontaloa_emenda_print.html`,
`_templates/v2018/loa/prestacaocontaloa_ajuste_print.html`, `_templates/v2018/crud/gate.html`,
`_frontend/v2018/src/routers.js`
Testes: `cmj/search/tests.py`, `cmj/loa/tests/test_prestacao_contas_tela.py`,
`cmj/loa/tests/test_prestacao_contas_consulta.py`, `cmj/core/test_recaptcha.py`

Lado Django da URL `/loa/<pk>/prestacaoconta`: o que acontece do recebimento da requisição até a
entrega da página ao v2018, e o caminho alternativo `?print=True`, que passa pelo reCAPTCHA e gera o
relatório para impressão. O painel Vue que a página carrega está em
[prestacao-contas-painel.md](./prestacao-contas-painel.md) (`LOA-PCL`).

As regras são `[observado]`, exceto LOA-PCT-007 e 063 a 070, implementadas, e LOA-PCT-002, 014, 057
e 060, acordadas. As observadas descrevem o que o código faz hoje e não foram confirmadas como regra
de negócio. Foram obtidas por leitura do código. As marcadas com "(executado)" também foram
conferidas em 2026-11-21 no banco de desenvolvimento, como anônimo, com `django.test.Client` na rota
real e a sessão do banco em somente leitura. Onde o reCAPTCHA impede a execução, a validação
`_validate_recaptcha` foi substituída em memória por uma que aceita (`mock.patch`), sem chamar o
Google e sem alterar arquivos.

Não foi executado:

- A validação real do reCAPTCHA junto ao Google (LOA-PCT-017 a 019).
- O JavaScript do relatório e a impressão pelo navegador: não havia navegador.
- Casos com LOA não publicada na base de desenvolvimento, onde as nove LOAs estão publicadas:
  LOA-PCT-064 foi conferida nos testes, com LOAs criadas no banco de testes.
- O `dev-webpack-stats.json` local estava em `compile`, com o dev server parado. As execuções
  apontaram o `webpack_loader`, só em memória, para o `webpack-stats.json` do build.

## Escopo

- A rota e a ordem de execução de `PrestacaoContaView` (`dispatch`, `get`, contexto, template).
- `GoogleRecapthaViewMixin`, como esta view o usa.
- O modo `print`: filtros, contexto, `InfoFilterMixin.infofilter` e os três templates do relatório.
- `prestacaoconta_detail.html` e a passagem para a rota `prestacaoconta_route` do v2018.

## Regras

### Rota e acesso

- LOA-PCT-001 [observado] A URL é `/loa/<int:pk>/prestacaoconta`, sem barra final, com o nome
  `cmj.loa:prestacaoconta_detail`. É registrada antes das rotas do CRUD de `Loa`, junto com
  `/loa/atual` e `/loa/<pk>/despesas`. Evidência: `cmj/loa/views/v_loa.py:72-81`,
  `cmj/loa/urls.py:12-15`.
- LOA-PCT-002 [acordado] `PrestacaoContaView` é declarada dentro de `LoaCrud`, mas a rota usa a
  classe direto (`LoaCrud.PrestacaoContaView.as_view()`), sem passar pelo `_add_base` do `Crud`.
  A view não recebe o atributo `crud` nem herda `LoaCrud.BaseMixin` (`LoaContextDataMixin` e
  `CrudBaseMixin`). Aceito em 2026-11-23: a prestação de contas é uma
  página própria, de painel, e não uma tela de CRUD da LOA; a conferência de acesso é feita pela
  própria view (LOA-PCT-064). Evidência: `cmj/loa/views/v_loa.py:75-79`, `sapl/crud/base.py:1125-1141`.
- LOA-PCT-003 [observado] A herança é `InfoFilterMixin`, `GoogleRecapthaViewMixin`,
  `Crud.DetailView`, com `model = Loa`. Evidência: `cmj/loa/views/v_loa.py:875-878`.
- LOA-PCT-004 [observado] `permission_required = ()` torna a view pública: sem permissão exigida,
  `has_permission` devolve `True` para qualquer usuário, inclusive anônimo. Evidência:
  `cmj/loa/views/v_loa.py:876`, `sapl/crud/base.py:206-213`.
- LOA-PCT-005 [observado] Como a view não tem `crud`, `container_field` é `None` e o `dispatch` do
  CRUD não aplica nenhum filtro por dono. Evidência: `sapl/crud/base.py:222-255`.
- LOA-PCT-006 [observado] A view aceita só `GET`, `HEAD` e `OPTIONS`. `POST` sem `print=True` na
  query string responde 405 (executado). Evidência: `cmj/loa/views/v_loa.py:875`,
  `cmj/mixins.py:623`.
- LOA-PCT-007 [implementado] `/loa/atual`, o link "Emendas Impositivas" da barra lateral do portal,
  redireciona para a prestação de contas da LOA de maior ano entre as publicadas que têm ao menos
  uma emenda, e responde 404 se não houver nenhuma. Não exige norma: enquanto a LOA do exercício
  seguinte tramita, o link acaba na página de detalhe dela (LOA-PCT-064), com as emendas ainda em
  proposta, e volta à prestação de contas quando ela vira norma. Aceito em 2026-11-23 como o
  comportamento desejado. Na base de desenvolvimento o destino é a LOA 2027 (executado). Evidência:
  `cmj/loa/views/v_loa.py:48-55`, `_templates/v2018/base_sidebar.html:35-40`.
- LOA-PCT-008 [observado] O item "Prestação de Contas" do subnav da LOA aponta para esta rota.
  Evidência: `_templates/v2018/loa/subnav.yaml:4-5`.

### Execução inicial (sem `print=True`)

- LOA-PCT-009 [observado] A ordem do `dispatch` é: o da própria view, que confere a LOA
  (LOA-PCT-064); o do reCAPTCHA, que não é acionado sem `print=True`; o do CRUD, que checa a
  permissão; e por fim o `get`. Evidência: `cmj/loa/views/v_loa.py:904-916`, `cmj/mixins.py:603-623`,
  `sapl/crud/base.py:222-255`.
- LOA-PCT-010 [retirada] Substituída por LOA-PCT-064.
- LOA-PCT-011 [retirada] Substituída por LOA-PCT-064.
- LOA-PCT-012 [retirada] Substituída por LOA-PCT-064.
- LOA-PCT-064 [implementado] Antes da tela, do gate do reCAPTCHA e do relatório, a view confere a
  LOA do `pk`. A que não existe, ou que o usuário não vê, responde 404 nos três: a visibilidade é a
  da lista de LOAs (LOA-LST-006), com anônimo e conta comum vendo só LOA publicada. A LOA visível
  cuja matéria não existe ou não virou norma redireciona para o detalhe da LOA, também nos três;
  na base de desenvolvimento é o caso da LOA 2027 (302 para `/loa/2027`, executado). Assim o gate
  só aparece para quem vai receber o relatório. Evidência: `cmj/loa/views/v_loa.py:904-916`,
  `cmj/loa/services/s_visibilidade.py:64-67`.
- LOA-PCT-013 [observado] Passadas as checagens, o `get` do CRUD busca a LOA de novo pelo `pk` e
  monta o contexto só com `object` e `loa`, sem listagem, porque não há `model_set`. Evidência:
  `sapl/crud/base.py:936-947`, `sapl/crud/base.py:966-994`.
- LOA-PCT-014 [acordado] O contexto ganha `path = " prestacaoconta-detail"`. As classes
  `container container-loa` e a troca do subnav para `subnav_loa_em_tramitacao.yaml` são de
  `LoaContextDataMixin`, que esta view não herda. Evidência: `cmj/loa/views/v_loa.py:918-922`,
  `cmj/loa/views/v_mixins.py:6-9`.
- LOA-PCT-015 [observado] A resposta é 200 com `loa/prestacaoconta_detail.html`, sem cookie novo
  para anônimo (executado na LOA 2026). Evidência: `cmj/loa/views/v_loa.py:878`.

### reCAPTCHA

- LOA-PCT-016 [observado] O gate é acionado só quando a query string traz `print` com o valor
  exato `True`. `print=true` e `print=False` seguem para a tela normal (executado). Evidência:
  `cmj/loa/views/v_loa.py:880-881`, `cmj/mixins.py:562-570`.
- LOA-PCT-017 [observado] Fora do modo de desenvolvimento (LOA-PCT-065), `GET` com `print=True` não
  gera o relatório: responde 200 com `crud/gate.html`, que mostra o widget do reCAPTCHA, o título
  "Gerar Relatório de Prestação de Contas das Emendas Impositivas", o botão "Acessar Conteúdo" e o
  link "Retornar" (LOA-PCT-068). Evidência: `cmj/mixins.py:605-612`, `cmj/mixins.py:572-586`,
  `cmj/loa/views/v_loa.py:882-884`, `_templates/v2018/crud/gate.html:17-48`.
- LOA-PCT-068 [implementado] O link "Retornar" do gate volta à prestação de contas da mesma LOA, com
  os filtros que estavam aplicados: é a URL do pedido sem o `print`. Evidência:
  `cmj/loa/views/v_loa.py:887-894`, `_templates/v2018/crud/gate.html:40-43`.
- LOA-PCT-065 [implementado] Com `DEBUG` ligado, o que só vale em desenvolvimento, o gate do
  reCAPTCHA é dispensado: `GET` com `print=True` devolve o relatório direto. A conferência da LOA
  (LOA-PCT-064) continua valendo. A dispensa está no `GoogleRecapthaViewMixin` e alcança as outras
  views que o usam com método de sucesso (o PDF da listagem de emendas e o download de matéria). Em
  produção `DEBUG` é falso e o gate vale. Evidência: `cmj/mixins.py:605-612`.
- LOA-PCT-018 [retirada] Substituída por LOA-PCT-064.
- LOA-PCT-019 [observado] O formulário do gate envia `POST` para a mesma URL com a query string
  inteira (`request.get_full_path()`), com `csrf_token`. Os filtros viajam na query string, não no
  corpo. Evidência: `cmj/mixins.py:575`, `_templates/v2018/crud/gate.html:31-32`.
- LOA-PCT-020 [observado] No `POST`, sem o campo `g-recaptcha-response` o gate volta com
  "Verificação do reCAPTCHA não efetuada.", sem chamar o Google (executado). Com o campo, a view
  consulta `https://www.google.com/recaptcha/api/siteverify` por `POST` (LOA-PCT-069). Falha de
  rede, resposta ilegível ou `success` falso voltam ao gate com "Ocorreu um erro na validação do
  reCAPTCHA.". Evidência: `cmj/mixins.py:588-601`, `cmj/mixins.py:613-618`.
- LOA-PCT-069 [implementado] A consulta ao Google fica numa função só, `recaptcha_confirmado`: a
  chave secreta e a resposta do usuário vão no corpo da requisição, e não na URL, e a chamada tem
  tempo limite de 5 segundos, sem novas tentativas. Sem resposta nesse tempo, com falha de rede ou
  com resposta fora do formato, a validação é recusada e a pessoa recebe a mensagem de erro. Usam a
  função as três views com `GoogleRecapthaViewMixin` e os formulários com reCAPTCHA: recuperação de
  senha, acompanhamento de matéria e de documento administrativo, e denúncia da ouvidoria.
  Evidência: `cmj/mixins.py:452-487`, `cmj/mixins.py:588-601`, `cmj/mixins.py:527-530`,
  `cmj/ouvidoria/forms.py:154-157`.
- LOA-PCT-021 [observado] Validado o reCAPTCHA, o `dispatch` chama `print()` e devolve a resposta
  dele. O `get` e a checagem de permissão do CRUD não rodam nesse caminho; a conferência da LOA
  (LOA-PCT-064) roda antes. Evidência: `cmj/mixins.py:619-622`, `cmj/loa/views/v_loa.py:885`.
- LOA-PCT-022 [observado] As chaves vêm de `GOOGLE_RECAPTCHA_SITE_KEY` e
  `GOOGLE_RECAPTCHA_SECRET_KEY`, com default vazio. Com a chave secreta vazia a validação depende da
  resposta do Google (não executado). Evidência: `cmj/settings/auth.py:37-40`,
  `cmj/mixins.py:471-482`.
- LOA-PCT-023 [observado] Cada relatório exige um reCAPTCHA novo: a validação não fica guardada em
  sessão nem em cookie. Evidência: `cmj/mixins.py:603-623`.

### Modo print: conjunto e filtros

- LOA-PCT-024 [retirada] Substituída por LOA-PCT-064.
- LOA-PCT-025 [retirada] Substituída por LOA-PCT-066 e LOA-PCC-070.
- LOA-PCT-026 [retirada] Substituída por LOA-PCT-066 e LOA-PCC-001.
- LOA-PCT-027 [retirada] Substituída por LOA-PCT-066.
- LOA-PCT-028 [observado] O filtro `situacao` aceita valores separados por vírgula. Para emendas:
  `REGISTRADO` é a fase 30 (aprovada), `IMPEDIMENTO` a 40, `EM_EXECUCAO` a 60 e `FINALIZADO` a 99.
  Para ajustes, os mesmos nomes levam às fases registrado, impedido, em execução e finalizado do
  ajuste. Nenhum valor reconhecido, ou os quatro juntos, não filtra. Evidência:
  `cmj/api/forms.py:74-111`, `cmj/api/forms.py:173-209`.
- LOA-PCT-029 [observado] O filtro `search` com um único termo numérico busca pelo número da matéria
  (emendas) ou pelo número do registro (ajustes). Nos demais casos exige todos os termos no campo
  `search` do model, sem acento e sem diferenciar caixa. Evidência: `cmj/api/forms.py:113-128`,
  `cmj/api/forms.py:155-171`.
- LOA-PCT-030 [retirada] Substituída por LOA-PCC-002.
- LOA-PCT-031 [observado] `tipo__in` aceita os tipos separados por vírgula num parâmetro só, que é a
  forma que o painel envia; repetido (`tipo__in=10&tipo__in=99`), valem todos. Evidência:
  `cmj/loa/views/v_loa.py:931-941`.
- LOA-PCT-032 [retirada] Substituída por LOA-PCT-066.

### Modo print: contexto e `InfoFilterMixin`

- LOA-PCT-033 [observado] O contexto do relatório tem `emendaloa_list` e `registroajusteloa_list`,
  `loa_title` e `infofilter`. Não tem `object`, e por isso o subnav da LOA não aparece. Evidência:
  `cmj/loa/views/v_loa.py:964-971`, `cmj/core/templatetags/menus.py:176-185`.
- LOA-PCT-034 [observado] `loa_title` é "Prestação de Contas das Emendas Impositivas", uma quebra de
  linha e o `str` da LOA da rota (LOA-PCT-070). Evidência: `cmj/loa/views/v_loa.py:967-970`.
- LOA-PCT-070 [implementado] No título do relatório, o nome da LOA sai como texto: a única marcação
  é a quebra de linha entre o título e o nome. Evidência: `cmj/loa/views/v_loa.py:967-970`,
  `_templates/v2018/loa/prestacaoconta_print.html:173`.
- LOA-PCT-035 [observado] `infofilter` é montado com o formulário do filterset das emendas, ou com o
  dos ajustes quando só os ajustes entram (`ajustes=True` sem `tipo__in`), caso em que
  `parlamentares` é lido como `parlamentares_valor`. Com `ajustes=True` o texto ganha "- Registros
  de Ajuste Técnico", e com mais de um exercício, a linha "Exercícios" com os anos. Evidência:
  `cmj/loa/views/v_loa.py:973-1008`.
- LOA-PCT-066 [implementado] O relatório usa a mesma seleção das consultas do painel
  (`PrestacaoContaService`, LOA-PCC-070): os mesmos filtros, lidos da query string da página
  (`situacao`, `unidade`, `entidade`, `parlamentares`, `search`, `tipo__in`, `ajustes` e `loas`), as
  mesmas condições de exercício e a mesma regra de valor. Cobre os exercícios extras selecionados no
  painel. Filtro inválido responde 400 com uma mensagem, e não mais erro 500. Parâmetros que não são
  filtro, como `print` e `view`, são ignorados. Evidência: `cmj/loa/views/v_loa.py:924-962`.
- LOA-PCT-036 [observado] `InfoFilterMixin.infofilter` percorre os dados limpos do formulário e
  ignora os campos vazios, `ordenacao` e `tipo_listagem`. Para cada campo restante gera
  `<strong>rótulo:</strong> valor`, e o valor depende do tipo do campo:
  - campo com queryset (parlamentar, unidade, entidade): o `str` de cada objeto escolhido, separados
    por " / ";
  - booleano: "Sim" ou "Não";
  - campo de escolha: o rótulo da escolha;
  - campo `<nome>__in` com lista: o rótulo das choices do campo do model, quando existem, ou os
    valores separados por vírgula;
  - `autoria_is`: o nome do autor (não usado por esta view);
  - qualquer outro, como `search` e `situacao`: o valor recebido.

  Havendo ao menos um filtro, a lista começa com "FILTROS APLICADOS". Os itens são unidos por
  `<br>`. Evidência: `cmj/search/views.py:109-195`.
- LOA-PCT-037 [retirada] Substituída por LOA-PCT-067.
- LOA-PCT-067 [implementado] No texto dos filtros do relatório, as situações saem com o nome legível
  ("Registrado", "Impedimento", "Em Execução" e "Finalizado"), separadas por vírgula e espaço:
  `situacao=EM_EXECUCAO,REGISTRADO` aparece como "Situação: Em Execução, Registrado". Evidência:
  `cmj/loa/views/v_loa.py:897-902`, `cmj/loa/views/v_loa.py:976-983`.
- LOA-PCT-038 [observado] O template emite `infofilter` e `loa_title` com `|safe`. Evidência:
  `_templates/v2018/loa/prestacaoconta_print.html:173`,
  `_templates/v2018/loa/prestacaoconta_print.html:186-188`.
- LOA-PCT-063 [implementado] No texto de `infofilter`, rótulos e valores saem como texto, com os
  caracteres de marcação convertidos em entidades. A marcação se limita ao negrito do título e dos
  rótulos e à quebra de linha entre os itens. Vale para as três telas que usam o método: este
  relatório e as buscas de matérias e de normas. Evidência: `cmj/search/views.py:111-114`,
  `cmj/search/views.py:195`. Teste: `cmj/search/tests.py`.

### Relatório: página

- LOA-PCT-039 [observado] O relatório estende `base.html`, esvazia o bloco `appvue_content` (não
  monta o Vue) e usa `loa_title`, sem a quebra de linha, como título da aba. Evidência:
  `_templates/v2018/loa/prestacaoconta_print.html:1-9`.
- LOA-PCT-040 [observado] O cabeçalho mostra o brasão, o nome da casa, "Poder Legislativo",
  `loa_title` e um botão "Salvar como PDF ou Imprimir em impressora", que chama `window.print()`. O
  servidor não gera PDF: a saída em papel ou PDF é a impressão do navegador. Evidência:
  `_templates/v2018/loa/prestacaoconta_print.html:157-183`.
- LOA-PCT-041 [observado] Abaixo do cabeçalho ficam o texto dos filtros aplicados e sete caixas
  "Exibir seções", todas marcadas: Prestação de Contas, Resumo de Empenhos, Detalhes de Empenhos,
  Ajustes Técnicos vinculados à Emenda, Registros Contábeis, Tramitações da Matéria e Documentos
  Acessórios. Desmarcar uma caixa esconde, na tela e na impressão, todo elemento com a classe
  `container-loa-*` correspondente. A escolha é só do navegador: não vai ao servidor nem é guardada.
  Evidência: `_templates/v2018/loa/prestacaoconta_print.html:184-231`,
  `_templates/v2018/loa/prestacaoconta_print.html:241-254`.
- LOA-PCT-042 [observado] Na impressão, o CSS esconde navegação, cabeçalho e rodapé do portal,
  botões e as caixas de seção. Evidência: `_templates/v2018/loa/prestacaoconta_print.html:32-37`.
- LOA-PCT-043 [observado] O corpo são dois parciais, emendas e depois ajustes. Cada um só emite algo
  se a sua lista existe e não é vazia. Com as duas vazias, o relatório mostra o cabeçalho e as
  caixas, sem aviso de "nenhum registro" (executado). Evidência:
  `_templates/v2018/loa/prestacaoconta_print.html:234-236`,
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:6`,
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:6`.

### Relatório: emendas

- LOA-PCT-044 [observado] A seção "Emendas Impositivas / Modificativas" tem um bloco numerado por
  emenda. O título do bloco é um link para o detalhe da emenda, com a epígrafe da matéria (se
  houver), o tipo e a fase. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:7-19`.
- LOA-PCT-045 [observado] Os dados gerais são: parlamentares (ou "Não informado"), valor original,
  unidade orçamentária, entidade e finalidade. A finalidade exibida é `ementa_format`, a frase
  montada pelo model, e não o campo digitado. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:21-44`,
  `cmj/loa/models/m_emendaloa.py:354-373`.
- LOA-PCT-046 [observado] A emenda que vale zero mostra "Valor Final: R$ 0,00" com o motivo: valor
  remanejado para os registros de ajuste, ou impedimento técnico (LOA-PCC-010). Antes o campo se
  chamava "Valor Redefinido" e nunca aparecia, por um erro na marcação das emendas com ajuste.
  (executado) Na LOA 2026 o relatório passou a mostrar a linha em 75 emendas, e o restante do HTML
  ficou idêntico ao anterior. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:30-33`,
  `cmj/loa/services/s_prestacaoconta.py:754-761`.
- LOA-PCT-047 [observado] A entidade aparece pelo nome fantasia, seguido do CNES, se houver, ou
  senão do CPF/CNPJ. Evidência: `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:38-41`.
- LOA-PCT-048 [observado] O bloco "Prestação de Contas (N)" aparece quando a emenda tem registros
  de prestação. Cada linha traz a data de envio do lote, a situação, os arquivos gerais do lote e o
  detalhamento do registro, com link para o detalhe e os arquivos próprios do registro. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:47-91`.
- LOA-PCT-049 [observado] O bloco "Empenhos (N)" aparece quando a emenda tem empenhos vinculados.
  Tem uma tabela de totais (empenhado, liquidado, pago bruto e anulado), que conta cada empenho uma
  vez, e uma tabela de detalhes, com uma linha por vínculo: código, data, fornecedor, CPF/CNPJ,
  modalidade, histórico e dotação, e os quatro valores. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:98-152`,
  `cmj/loa/models/m_financeiro_execucao.py:360-397`.
- LOA-PCT-050 [observado] O bloco "Ajustes Técnicos (N)" lista os registros de ajuste ligados à
  emenda: identificação, ofício, fase, unidade, descrição e valor. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:159-185`.
- LOA-PCT-051 [observado] O bloco "Registros Contábeis (N)" lista o `str` de cada registro contábil
  da emenda. Evidência: `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:190-198`.
- LOA-PCT-052 [observado] Só para emenda com matéria, aparecem "Tramitações (N)" (data, status,
  unidade local e destino, texto) e "Documentos Acessórios (N)" (nome com link para o arquivo, tipo,
  data, autor e ementa). Evidência:
  `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:202-257`.

### Relatório: ajustes

- LOA-PCT-053 [observado] A seção "Ajustes Técnicos" tem um bloco numerado por registro, com link
  para o detalhe, identificação, tipo e fase. Os dados gerais são: parlamentares do ofício (não os
  do registro), valor total, unidade, entidade e descrição. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:7-40`.
- LOA-PCT-054 [observado] Seguem os blocos "Emendas Impositivas Relacionadas", "Prestação de Contas
  (N)" e "Empenhos (N)", os dois últimos com a mesma estrutura dos blocos da emenda. Evidência:
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:43-51`,
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:55-98`,
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:104-160`.
- LOA-PCT-055 [observado] Os links de arquivo do relatório não apontam para a mídia: `arquivo.url`
  devolve a rota da action `arquivo` da API do model, ou vazio quando não há arquivo. Evidência:
  `sapl/utils.py:292-310`, `cmj/api/loa/views/arquivoprestacaocontaloa.py:7-9`.
- LOA-PCT-056 [observado] Os dois parciais não usam `|safe`: todo texto vindo do banco sai com
  escape. Evidência: `_templates/v2018/loa/prestacaocontaloa_emenda_print.html:4`,
  `_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:4`.
- LOA-PCT-057 [acordado] O relatório é gerado a cada pedido, sem cache, e a proteção contra
  repetição é o reCAPTCHA, um por relatório (dispensado só com `DEBUG` ligado, LOA-PCT-065). Aceito
  em 2026-11-23: o custo no banco não cresce com a quantidade de itens (LOA-PCC-070), e guardar o
  relatório atrasaria a exibição de uma prestação de contas recém-registrada. (executado em
  2026-11-23) O relatório completo da LOA 2026 tem 3 MB, leva 3,5 s e faz 328 consultas, 281 delas
  do menu do portal; antes de usar o serviço levava 12,7 s e fazia 2.601. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:670-803`, `cmj/mixins.py:605-612`.

### Página do painel e passagem para o v2018

- LOA-PCT-058 [observado] `prestacaoconta_detail.html` estende `crud/list.html`, troca a classe do
  contêiner principal por `container` mais o `path` do contexto, esvazia o bloco `appvue_content`
  de `base.html` e recoloca `<div id="app"><App/></div>` dentro de `base_content`, no lugar do
  conteúdo do CRUD. Evidência: `_templates/v2018/loa/prestacaoconta_detail.html:1-7`,
  `_templates/v2018/base.html:119-123`.
- LOA-PCT-059 [observado] Título, subnav e mensagens continuam vindo de `base.html`: o `<h2>` mostra
  o `str` da LOA (`object`) e o subnav é `loa/subnav.yaml` (executado). Evidência:
  `_templates/v2018/base.html:60`, `_templates/v2018/base.html:72-82`.
- LOA-PCT-060 [acordado] A página carrega só a entrada `app` do v2018. `crud/list.html` carregaria
  também a entrada indicada em `view.crud.frontend` (`loa`), mas a view não tem `crud`
  (LOA-PCT-002). Evidência: `_templates/v2018/crud/list.html:5-16`,
  `cmj/loa/views/v_loa.py:41`.
- LOA-PCT-061 [observado] A entrada `app` monta o Vue em `#app`, com roteador em modo `history`. O
  roteador casa a URL do navegador com `/loa/:pkloa(\d+)/prestacaoconta` (`prestacaoconta_route`),
  filha de `/loa/`, e carrega `PrestacaoContaLoaLayout` sob demanda dentro de `LoaLayout`. A mesma
  URL é, portanto, rota do Django e rota do Vue, e o `pk` chega ao painel como `pkloa`. Evidência:
  `_frontend/v2018/src/main.js:40-51`, `_frontend/v2018/src/routers.js:7-26`,
  `_frontend/v2018/src/modules/loa/LoaLayout.vue:1-5`.
- LOA-PCT-062 [observado] O Django não passa dados ao painel pelo HTML: tudo o que o painel mostra
  vem da API. A query string da URL é lida só pelo Vue, salvo `print=True` (LOA-PCT-016).
  Evidência: `_templates/v2018/loa/prestacaoconta_detail.html:5-7`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1 a 7 de `docs/specs/README.md`, revista em 2026-11-23.

Nenhum risco em aberto (2026-11-23). Itens sem achado: 3 (a view não monta caminho de arquivo nem
serve mídia), 4 (sem `subprocess`, SQL cru ou template a partir de texto do usuário) e 5 (sem cache,
índice ou log próprios). O nome e o CPF/CNPJ do fornecedor de cada empenho, que o relatório exibe,
foram aceitos como dado público em 2026-11-23 (LOA-PCL-087).

## Dúvidas

Nenhuma dúvida em aberto (2026-11-23).

## Pendências encontradas

Incoerências pequenas do relatório, por leitura, sem decisão de negócio envolvida:

- "Eviado em lote" no parcial de ajustes (`_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:58`).
- O bloco "Emendas Impositivas Relacionadas" não tem caixa em "Exibir seções" e não pode ser
  escondido (`_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:44`).
- Desmarcar as duas caixas de empenhos deixa o título "Empenhos (N)" sem tabela: as classes estão
  nas tabelas, não no bloco (`_templates/v2018/loa/prestacaocontaloa_emenda_print.html:99-102`).
- "Empenhos (N)" e a tabela de detalhes contam vínculos, e os totais contam empenhos distintos
  (`cmj/loa/models/m_financeiro_execucao.py:360-397`).
- O "Valor Total" do ajuste usa a soma bruta mesmo em impedimento técnico
  (`_templates/v2018/loa/prestacaocontaloa_ajuste_print.html:28-29`).
- Arquivo ausente gera link com `href` vazio e texto clicável (`sapl/utils.py:309-310`).
- O menu do portal faz 281 consultas em cada página que usa o template base, o relatório inclusive
  (tabela `sigad_classe`, executado em 2026-11-23). É de todo o portal, fora deste recorte.

## Fora do escopo

- O painel Vue e a API que ele consome: [prestacao-contas-painel.md](./prestacao-contas-painel.md).
- Os outros usos de `InfoFilterMixin` (buscas de matérias e normas) e de `GoogleRecapthaViewMixin`.
- Os CRUDs de registro da prestação de contas (`cmj/loa/views/v_prestacaoconta.py`) e as actions
  `arquivo` da API.
- O cálculo de `ementa_format`, das fases e dos valores da emenda: `fases-emenda.md` e
  `edicao-emenda.md`.
- A estrutura do v2018 (entradas, `webpack_loader`, `App`): `docs/specs/v2018/estrutura.md`.
