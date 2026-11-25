# LOA: cadastro, lista e detalhe da LOA (`LoaCrud`)

Status: observado, com vinte e uma regras implementadas (LOA-CRUD-014, 020, 027, 033, 036, 039,
043, 046, 049, 054, 057, 058, 061, 064, 065 a 067, 069 a 071) e uma acordada (LOA-CRUD-056)
Última verificação: 2026-11-24 (commit `934979248`)
Código principal: `cmj/loa/views/v_loa.py` (`LoaCrud`, exceto `PrestacaoContaView`),
`cmj/loa/forms/f_ajusteloa.py`, `cmj/loa/models/m_ajusteloa.py`,
`cmj/loa/views/v_mixins.py`, `cmj/loa/forms/f_loa.py`, `cmj/loa/forms/f_mixins.py`,
`cmj/loa/services/s_loa.py`, `cmj/loa/models/m_loa.py`, `_templates/v2018/loa/layouts.yaml`,
`_templates/v2018/loa/widget_loaparlamentar_set_list.html`,
`_templates/v2018/loa/emendaloa_totalize_unidade.html`,
`_templates/v2018/loa/emendaloa_totalize_entidade.html`
Testes: `cmj/loa/tests/test_crud_loa.py`

O que acontece nas telas `/loa` (lista), `/loa/create`, `/loa/<pk>/edit`, `/loa/<pk>/delete` e
`/loa/<pk>` (detalhe), nas rotas extras `/loa/atual` e `/loa/<pk>/despesas`, e no cálculo da
disponibilidade de cada parlamentar (`LoaService.update_disponibilidades`), que alimenta o detalhe.
O centro da spec é o detalhe e seus três resumos: por parlamentar
(`hook_resumo_emendas_impositivas`), por unidade orçamentária (`hook_resumo_unidades`) e por
entidade (`hook_resumo_entidades`).

As regras são `[observado]`, exceto as implementadas (LOA-CRUD-014, 020, 027, 033, 036, 039,
043, 046, 049, 054, 057, 058, 061, 064, 065 a 067, 069 a 071), a acordada (LOA-CRUD-056) e as
retiradas (LOA-CRUD-016, 026, 028 a 031, 047, 051, 052, 062 e 068). As observadas descrevem o que o
código faz hoje e não foram confirmadas como regra de negócio. Foram obtidas por leitura do código.
As marcadas com "(executado)" também foram conferidas em 2026-11-24 no banco de desenvolvimento, com
a sessão do PostgreSQL em somente leitura, como anônimo, com `django.test.Client` na rota real. O
banco de desenvolvimento não tem emenda na fase -10, emenda impositiva sem participação de
parlamentar, ajuste de valor negativo, LOA não publicada nem LOA posterior a 2022 sem parlamentares:
as regras sobre esses casos ficaram só na leitura.

Não existe classe que herde de `LoaCrud` ou de suas classes internas. As "subclasses" desta spec são
as classes internas `BaseMixin`, `ListView`, `CreateView`, `UpdateView` e `DetailView`, e a
`DeleteView` herdada de `Crud`.

## Escopo

- Rotas, permissões e visibilidade de `LoaCrud`.
- Lista de LOAs: colunas, visibilidade e redirecionamento.
- Formulário de criação e edição (`LoaForm`) e o que ele grava.
- `LoaService.update_disponibilidades`, chamado pelo formulário e por todo `EmendaLoa.save`.
- Detalhe: layout, cabeçalho, disponibilidades e os três resumos, com cada passo do cálculo.
- Exclusão.

## Regras

### Rotas e acesso

- LOA-CRUD-001 [observado] `LoaCrud` é o `Crud` do model `Loa` com `public = [RP_LIST, RP_DETAIL]`:
  lista e detalhe não exigem permissão, e criar, editar e excluir exigem `loa.add_loa`,
  `loa.change_loa` e `loa.delete_loa`. Evidência: `cmj/loa/views/v_loa.py:36-40`,
  `sapl/crud/base.py:1113-1123`.
- LOA-CRUD-002 [observado] O grupo de operador da LOA recebe as cinco permissões de `Loa`, e o
  terceiro elemento da regra torna lista e detalhe públicos também na API e no WebSocket.
  Evidência: `cmj/globalrules/map_rules.py:241-244`, `cmj/globalrules/map_rules.py:53-56`.
- LOA-CRUD-003 [observado] As rotas `/loa/atual`, `/loa/<pk>/despesas` e `/loa/<pk>/prestacaoconta`
  são registradas antes das rotas do CRUD. Evidência: `cmj/loa/views/v_loa.py:72-80`.
- LOA-CRUD-004 [observado] `/loa/atual` redireciona para a prestação de contas da LOA publicada de
  maior ano que tenha ao menos uma emenda de fase maior que zero (LOA-CRUD-065), e devolve 404 com
  "Nenhuma LOA publicada encontrada." quando não há. Evidência: `cmj/loa/views/v_loa.py:47-55`.
- LOA-CRUD-005 [observado] `/loa/<pk>/despesas` só atende LOA publicada, para qualquer usuário, e
  devolve 404 nas demais. Renderiza `loa/despesas_espelho.html` com o subnav de LOA em tramitação,
  qualquer que seja a situação da matéria. Evidência: `cmj/loa/views/v_loa.py:57-70`.

### Base comum (lista, detalhe e formulários)

- LOA-CRUD-006 [observado] `frontend = "loa"`: as telas do CRUD carregam o bundle `loa` do v2018.
  Evidência: `cmj/loa/views/v_loa.py:40`.
- LOA-CRUD-007 [observado] A lista mostra ano, receita corrente líquida e os pares valor e
  percentual das disponibilidades total, saúde e diversos. A coluna `publicado` só aparece para
  usuário autenticado. Evidência: `cmj/loa/views/v_loa.py:85-97`.
- LOA-CRUD-008 [observado] Para anônimo, o link "voltar para a lista" fica vazio quando há no máximo
  uma LOA publicada. Evidência: `cmj/loa/views/v_loa.py:107-113`.
- LOA-CRUD-009 [observado] Todas as telas acrescentam `container container-loa` ao `path`. Quando a
  LOA tem matéria e a matéria ainda não virou norma, usam o subnav
  `loa/subnav_loa_em_tramitacao.yaml`; LOA sem matéria usa o subnav padrão. Qualquer exceção nessa
  escolha é descartada sem registro. Evidência: `cmj/loa/views/v_mixins.py:6-41`.

### Lista

- LOA-CRUD-010 [observado] Anônimo e conta comum veem só LOA publicada; quem tem
  `loa.emendaloa_full_editor` vê todas; operador de autor vê as publicadas e as cuja matéria ainda
  não virou norma, inclusive as sem matéria. É a mesma regra de `EmendaLoaService.loas_visiveis`.
  Evidência: `cmj/loa/views/v_loa.py:136-154`, `cmj/loa/services/s_emendaloa.py:250-271`.
- LOA-CRUD-011 [observado] Ordem decrescente de id, quatro LOAs por página, paginação estática.
  Evidência: `cmj/loa/models/m_loa.py:150`, `cmj/loa/views/v_loa.py:116-117`,
  `cmj/loa/views/v_loa.py:129-134`.
- LOA-CRUD-012 [observado] Quando o resultado tem exatamente uma LOA, a lista redireciona para o
  detalhe dela. Evidência: `cmj/loa/views/v_loa.py:119-127`.
- LOA-CRUD-013 [observado] A coluna ano leva ao detalhe e mostra um botão para a prestação de contas
  quando a matéria já virou norma, ou para as emendas quando não virou ou não há matéria.
  Evidência: `cmj/loa/views/v_loa.py:223-241`.
- LOA-CRUD-014 [implementado] A coluna da receita corrente líquida mostra " - " antes de 2023. Para
  ano futuro, mostra `rcl_previa` com "Processo Legislativo em andamento" ou "LOA Aprovada"; para o
  ano corrente, a RCL com "LOA em fase de Execução"; para ano passado, a RCL com "LOA executada em"
  seguido do ano. Evidência: `cmj/loa/views/v_loa.py:165-218`.
- LOA-CRUD-015 [observado] Os percentuais aparecem como "(x.x%)" ao lado do valor, sem cabeçalho
  próprio. Evidência: `cmj/loa/views/v_loa.py:156-163`, `cmj/loa/views/v_loa.py:243-253`.
- LOA-CRUD-016 [retirada] Havia `hook_btn_lista_emendas` e `hook_header_btn_lista_emendas`, nunca
  chamados, porque `btn_lista_emendas` não está nas colunas. Removida: os dois hooks saíram do
  código.

### Criação e edição

- LOA-CRUD-017 [observado] O formulário tem ano, RCL, matéria (por tipo, número e ano), publicado,
  os três percentuais, detalhamento de fonte, as três despesas padrão de dedução, parlamentares e
  observações de rodapé. Evidência: `cmj/loa/forms/f_loa.py:44-63`,
  `_templates/v2018/loa/layouts.yaml:2-8`.
- LOA-CRUD-018 [observado] A matéria é buscada por tipo, número e ano; se não existe, o formulário
  recusa; se falta um dos três, a LOA fica sem matéria. Na edição, os três campos vêm preenchidos
  com a matéria atual. Evidência: `cmj/loa/forms/f_mixins.py:23-62`,
  `cmj/loa/views/v_loa.py:280-286`.
- LOA-CRUD-019 [observado] Uma matéria só pode estar em uma LOA. Quando o formulário recusa a
  matéria, a tela mostra "Já existe Loa vinculada a Matéria Legislativa selecionada.", qualquer que
  seja o erro. Evidência: `cmj/loa/models/m_loa.py:19-27`, `cmj/loa/views/v_loa.py:258-268`,
  `cmj/loa/views/v_loa.py:288-298`.
- LOA-CRUD-020 [implementado] Os parlamentares oferecidos para vincular são os que têm mandato na
  legislatura do projeto ou na do ano da LOA, mais os já vinculados. Em LOA nova ainda sem ano, ou
  quando não há mandato registrado para o ano, são os ativos do cadastro. Evidência:
  `cmj/loa/forms/f_loa.py:70`, `cmj/loa/forms/f_loa.py:102-118`,
  `cmj/loa/services/s_loa.py:71-77`.
- LOA-CRUD-021 [observado] As despesas padrão de dedução são as da própria LOA com função 99 e fonte
  iniciada por 100 (diversos), 101 (educação) ou 102 (saúde); em LOA nova ou sem matéria, a lista
  fica vazia. Evidência: `cmj/loa/forms/f_loa.py:72-100`.
- LOA-CRUD-022 [observado] As observações de rodapé precisam ser YAML válido. Evidência:
  `cmj/loa/forms/f_loa.py:120-132`.
- LOA-CRUD-023 [observado] Ao salvar, cada disponibilidade da LOA é RCL × percentual / 100,
  truncada em centavos, calculada separadamente: o total não é forçado a ser saúde mais diversos.
  Enquanto não há norma, `rcl_previa` recebe a RCL; depois da norma, `rcl_previa` não muda mais.
  Evidência: `cmj/loa/forms/f_loa.py:134-160`.
- LOA-CRUD-024 [observado] Depois de salvar a LOA e os parlamentares, o formulário recalcula a
  disponibilidade de cada parlamentar (LOA-CRUD-027 e 070). Evidência:
  `cmj/loa/forms/f_loa.py:162-164`, `cmj/loa/models/m_loa.py:158-159`.

### Disponibilidade por parlamentar (`LoaService.update_disponibilidades`)

- LOA-CRUD-025 [observado] O recálculo roda ao salvar a LOA pelo formulário e a cada `save` de
  qualquer `EmendaLoa` da LOA. Evidência: `cmj/loa/forms/f_loa.py:164`,
  `cmj/loa/models/m_emendaloa.py:826-834`.
- LOA-CRUD-026 [retirada] O recálculo dependia de a LOA e a matéria estarem na legislatura atual.
  Substituída por LOA-CRUD-070.
- LOA-CRUD-027 [implementado] Cada parlamentar vinculado à LOA recebe a disponibilidade de saúde e a
  de diversos da LOA divididas pelo número de vinculados, truncadas em centavos, e o total é a soma
  das duas partes. Sem parlamentar vinculado, nada muda. A exceção é a LOA do primeiro ano de uma
  legislatura (LOA-CRUD-070). Evidência: `cmj/loa/services/s_loa.py:92-117`,
  `cmj/loa/services/s_loa.py:404-417`.
- LOA-CRUD-028 [retirada] O recálculo separava parlamentares ativos com e sem emenda e inativos com
  emenda. Substituída por LOA-CRUD-070.
- LOA-CRUD-029 [retirada] A prévia era reduzida ao maior múltiplo do número de ativos. Substituída
  por LOA-CRUD-070.
- LOA-CRUD-030 [retirada] O inativo com emenda recebia a prévia menos os seus impedimentos.
  Substituída por LOA-CRUD-070.
- LOA-CRUD-031 [retirada] O ativo recebia a disponibilidade, ou a diferença para a prévia, mais os
  impedimentos dos inativos. Substituída por LOA-CRUD-070.
- LOA-CRUD-068 [retirada] Sem parlamentar ativo no cadastro não havia recálculo. Substituída por
  LOA-CRUD-070.
- LOA-CRUD-070 [implementado] Na LOA do primeiro ano de uma legislatura, a divisão segue os mandatos,
  e não o campo `ativo` nem a data em que é feita. Até a RCL definitiva ser lançada, a
  disponibilidade é dividida entre os parlamentares originais (LOA-CRUD-069). Depois dela, por tipo:
  a prévia (`rcl_previa` × percentual / 100) é dividida pelo número de originais, e cada original
  fica com a sua parte, menos o valor das suas emendas hoje em impedimento técnico quando não tem
  mandato na legislatura nova; a diferença entre a disponibilidade da LOA e a prévia, somada a esses
  impedimentos, é dividida pelo número de vinculados com mandato na legislatura do ano da LOA, e
  cada um deles recebe uma parte. O reeleito recebe as duas partes. Só contam parlamentares
  vinculados à LOA; quem não tem mandato em nenhuma das duas legislaturas mantém o que tem. Sem
  mandato registrado numa das duas, vale LOA-CRUD-027. Os valores gravados nas LOAs de 2023 a 2027
  do banco de desenvolvimento são os mesmos que esta regra calcula (executado). Evidência:
  `cmj/loa/services/s_loa.py:79-153`.

### Detalhe: estrutura e acesso

- LOA-CRUD-032 [observado] O detalhe usa o layout `LoaDetail`: ano e matéria ou norma; RCL e as três
  disponibilidades; resumo por parlamentar; resumo por entidade; resumo por unidade. LOA de 2022 ou
  anterior usa `LoaDetailATE2022`, só com ano e matéria ou norma. Evidência:
  `_templates/v2018/loa/layouts.yaml:10-20`, `cmj/loa/views/v_loa.py:301`,
  `cmj/loa/views/v_loa.py:340-341`.
- LOA-CRUD-033 [implementado] O detalhe segue a visibilidade da lista (LOA-CRUD-010), pela mesma
  conferência da prestação de contas (`VisibilidadeLoaService.loa_visivel`): a LOA que o usuário não
  vê na lista responde 404, antes de qualquer cálculo. Evidência: `cmj/loa/views/v_loa.py:332-343`,
  `cmj/loa/services/s_visibilidade.py:64-67`, `cmj/loa/services/s_emendaloa.py:250-271`.
- LOA-CRUD-034 [observado] Cada campo do layout passa pelo `hook_<campo>` da view. Se o hook levanta
  exceção, é chamado de novo com os mesmos argumentos e, se falhar outra vez, uma terceira vez só
  com o objeto, já sem tratamento: um resumo com erro roda três vezes e termina em erro 500.
  Evidência: `sapl/crispy_layout_mixin.py:343-361`.
- LOA-CRUD-035 [observado] O texto devolvido pelos hooks é inserido sem escape (`|safe`). Nos três
  resumos, os nomes vindos do banco passam pelo escape automático dos templates. Evidência:
  `_templates/v2018/crud/detail_column_widget.html:41`,
  `_templates/v2018/loa/emendaloa_totalize_entidade.html:19-25`.
- LOA-CRUD-036 [implementado] O botão "Adicionar Emendas Impositivas" aparece quando a LOA não tem
  matéria ou a matéria não virou norma, para quem pode criar emenda: quem tem a permissão
  `loa.add_emendaloa` ou é operador de autor (`EmendaLoaService.pode_criar`, a mesma regra da
  criação). Evidência: `cmj/loa/views/v_loa.py:303-322`, `cmj/loa/services/s_emendaloa.py:239-246`.
- LOA-CRUD-037 [observado] Com norma, o campo matéria ou norma mostra "Norma Jurídica" com link para
  a norma; com matéria sem norma, o link da matéria, com a epígrafe curta no lugar do nome
  (`hook_materia`, que o `get_column` chama ao montar `materia|fk_urlize_for_detail`), e "Processo
  Legislativo em Andamento"; sem matéria, fica vazio. Evidência: `cmj/loa/views/v_loa.py:345-370`,
  `sapl/crispy_layout_mixin.py:332-347`.
- LOA-CRUD-038 [observado] A LOA está em execução quando `rcl_previa` difere da RCL. Em execução, o
  detalhe mostra a RCL com "RCL de" e o ano anterior ao da LOA; senão, `rcl_previa` com "RCL de" e
  o ano de dois anos antes. Evidência: `cmj/loa/views/v_loa.py:372-390`.
- LOA-CRUD-039 [implementado] Cada disponibilidade mostra o valor, o percentual e o "Valor por
  Parlamentar": a disponibilidade da LOA dividida, com truncamento, pelo número de parlamentares
  originais vinculados (LOA-CRUD-069). Sem nenhum, o valor por parlamentar não aparece. Evidência:
  `cmj/loa/views/v_loa.py:392-430`.

### Detalhe: resumo por parlamentar (`hook_resumo_emendas_impositivas`)

Notação por parlamentar e tipo: `disp` é a disponibilidade do parlamentar (LOA-CRUD-027 e 070),
`D` o já destinado bruto, `I` o impedimento bruto, `Ac` e `As` os ajustes com e sem emenda, `R` o
remanescente e `Aimp` os ajustes impedidos.

- LOA-CRUD-040 [observado] Há uma linha por parlamentar vinculado à LOA, primeiro os que têm mandato
  e depois os que não têm (LOA-CRUD-067), cada grupo em ordem de nome. Evidência:
  `cmj/loa/services/s_loa.py:248-250`, `cmj/loa/services/s_loa.py:294-295`.
- LOA-CRUD-041 [observado] Cada linha tem as colunas de Saúde (10) e de Diversos (99), os dois
  primeiros itens de `TIPOEMENDALOA_CHOICE`. Evidência:
  `cmj/loa/services/s_loa.py:179-180`,
  `cmj/loa/models/m_emendaloa.py:62-69`.
- LOA-CRUD-042 [observado] `D` é a soma das participações do parlamentar nas emendas da LOA do tipo
  em qualquer fase maior que zero (LOA-CRUD-065): inclui proposta e impedimento. Evidência:
  `cmj/loa/services/s_loa.py:195-208`.
- LOA-CRUD-043 [implementado] `I` é a soma das participações nas emendas impedidas: as que estão na
  fase 40 (impedimento técnico) ou têm registro de ajuste vinculado, a mesma regra da prestação de
  contas (LOA-PCC-010). A emenda que passou pelo impedimento e seguiu sem ajuste conta como
  destinada. Evidência:
  `cmj/loa/services/s_loa.py:186-208`,
  `cmj/loa/services/s_prestacaoconta.py:309-313`.
- LOA-CRUD-044 [observado] `Ac` é a soma dos ajustes do parlamentar em registros da LOA do mesmo
  tipo, vinculados a emenda desse tipo; `As`, a dos registros sem emenda. Os dois não filtram a fase
  do registro, e o valor do ajuste não é negativo (LOA-CRUD-066). O registro pode estar vinculado a
  várias emendas, e o valor do ajuste entra uma vez só. Evidência:
  `cmj/loa/services/s_loa.py:210-240`.
- LOA-CRUD-045 [observado] `R = disp − D`, e o resultado é: já destinado `= D − I + Ac + As`; sem
  destinação `= disp − D + I − Ac − As`; impedimento técnico `= I − Ac`. Evidência:
  `cmj/loa/services/s_loa.py:265-269`.
- LOA-CRUD-046 [implementado] Se o parlamentar tem mandato (LOA-CRUD-067) e a LOA tem norma, o
  impedimento técnico recebe mais `R − As`: o impedimento a sanar é o das emendas impedidas mais o
  remanescente, menos os ajustes (`I + R − Ac − As`). Para quem não tem mandato, fica `I − Ac`. Evidência:
  `cmj/loa/services/s_loa.py:271-275`.
- LOA-CRUD-047 [retirada] O impedimento técnico virava zero quando seu módulo era igual ao de `R` e
  havia algum ajuste. Removida: compensava o uso do campo `ativo` do cadastro, e o caso passou a ser
  coberto por LOA-CRUD-046 com LOA-CRUD-067.
- LOA-CRUD-048 [observado] Os totais de cada tipo são a soma das linhas. Evidência:
  `cmj/loa/services/s_loa.py:289-291`.
- LOA-CRUD-049 [implementado] `Aimp`, a soma dos ajustes do parlamentar no tipo com registro na fase
  40 (impedido), sai do já destinado e entra no impedimento técnico e no sem destinação, haja ou não
  registro de prestação de contas: o ajuste impedido fica na coluna de impedimento enquanto estiver
  nessa fase, como a emenda que volta ao impedimento depois de aprovada ou em execução
  (LOA-CRUD-043). Evidência:
  `cmj/loa/services/s_loa.py:277-281`.
- LOA-CRUD-050 [observado] Cada coluna de valor aparece quando o total dela é diferente de zero ou o
  usuário é superusuário. Quando a LOA tem registro de prestação de contas, as colunas de sem
  destinação não aparecem. O cabeçalho de cada tipo mostra o total já destinado. Evidência:
  `cmj/loa/views/v_loa.py:452-467`, `cmj/loa/services/s_loa.py:301-303`,
  `_templates/v2018/loa/widget_loaparlamentar_set_list.html:9-14`.
- LOA-CRUD-051 [retirada] O resumo somava empenhado, liquidado, pago bruto e anulado por
  parlamentar. Removida: a execução dos empenhos fica na prestação de contas (LOA-PCC).
- LOA-CRUD-052 [retirada] Só o superusuário via as colunas de execução do resumo. Removida: as
  colunas saíram com LOA-CRUD-051.
- LOA-CRUD-053 [observado] O nome do parlamentar leva à prestação de contas filtrada por ele, quando
  a LOA tem norma, ou à lista de emendas filtrada por ele; tem a etiqueta Ativo ou Inativo, pelo
  mandato (LOA-CRUD-067), e a disponibilidade total dele. Evidência:
  `_templates/v2018/loa/widget_loaparlamentar_set_list.html:30-45`.
- LOA-CRUD-054 [implementado] LOA sem parlamentar vinculado abre o detalhe com o resumo por
  parlamentar vazio e os totais zerados. Evidência:
  `cmj/loa/services/s_loa.py:242-246`.
- LOA-CRUD-055 [observado] Cada acesso ao detalhe faz 322 ou 323 consultas nas LOAs de 2023 a 2027
  do banco de desenvolvimento, como anônimo (executado em 2026-11-25): 13 são dos três resumos
  (LOA-CRUD-071) e cerca de 280 vêm do menu e do breadcrumb do portal, comuns a todas as páginas e
  fora desta spec. A medição é em desenvolvimento, onde nada fica em cache. Evidência:
  `cmj/loa/views/v_loa.py:441-529`.
- LOA-CRUD-071 [implementado] Os três resumos do detalhe são calculados no `LoaService`
  (`resumo_parlamentares`, `resumo_unidades` e `resumo_entidades`), e a view só monta as colunas que
  dependem de quem consulta (LOA-CRUD-050) e renderiza. O número de consultas não cresce com o de
  parlamentares, unidades ou entidades: as somas do resumo por parlamentar são agrupadas por
  parlamentar e tipo, em duas consultas para a LOA inteira, e a norma da matéria é consultada uma
  vez por acesso, não a cada linha dos templates. Os resumos não ficam em cache: cada acesso
  reflete o banco. Evidência: `cmj/loa/services/s_loa.py:155-402`,
  `cmj/loa/views/v_loa.py:441-529`.

### Detalhe: resumo por unidade orçamentária (`hook_resumo_unidades`)

- LOA-CRUD-056 [acordado] Soma as participações de cada parlamentar por unidade, nas emendas da LOA
  de Saúde e de Diversos com fase maior que zero, qualquer que seja, sem considerar impedimento nem
  ajustes: depois da aprovação, mostra o cenário com os valores originais das emendas aprovadas
  ("Totalização na aprovação, sem ajustes por impedimento técnico"); antes dela, totaliza as
  propostas, para acompanhar o processo legislativo. Vale também para o resumo por entidade
  (LOA-CRUD-060). Evidência:
  `cmj/loa/services/s_loa.py:306-325`,
  `cmj/loa/models/m_emendaloa.py:35-39`.
- LOA-CRUD-057 [implementado] Agrupa por unidade em ordem de especificação, com os parlamentares em
  ordem de nome, a soma da unidade e o total geral. As emendas sem unidade formam o grupo "Sem
  unidade orçamentária". Evidência: `cmj/loa/services/s_loa.py:327-351`,
  `_templates/v2018/loa/emendaloa_totalize_unidade.html:17-18`.
- LOA-CRUD-058 [implementado] A emenda impositiva sem participação de parlamentar entra nos resumos
  por unidade e por entidade com valor zero e uma linha de parlamentar sem nome. Evidência:
  `cmj/loa/services/s_loa.py:319-322`.
- LOA-CRUD-059 [observado] A unidade e cada parlamentar levam à lista de prestação de contas, quando
  a LOA tem norma, ou à de emendas, filtradas pela unidade e pelo parlamentar. O grupo sem unidade
  (LOA-CRUD-057) e os parlamentares dele ficam sem link. Sem emendas, a tabela fica vazia, sem
  total. Evidência: `_templates/v2018/loa/emendaloa_totalize_unidade.html:4-64`.

### Detalhe: resumo por entidade (`hook_resumo_entidades`)

- LOA-CRUD-060 [observado] Mesma base do resumo por unidade, agrupada por entidade, com o nome
  fantasia em maiúsculas. Emendas sem entidade ou com nome fantasia vazio são ignoradas, então o
  total geral pode ser menor que o do resumo por unidade. Evidência:
  `cmj/loa/services/s_loa.py:353-376`.
- LOA-CRUD-061 [implementado] Cada parlamentar aparece uma vez em cada entidade, com a soma das
  suas participações nas emendas dela, mesmo quando elas estão em unidades ou tipos diferentes, e os
  parlamentares da entidade saem em ordem de nome. Evidência:
  `cmj/loa/services/s_loa.py:378-401`.
- LOA-CRUD-062 [retirada] Emenda impositiva com entidade e sem participação de parlamentar
  terminava em erro. Substituída por LOA-CRUD-058.
- LOA-CRUD-063 [observado] A entidade e cada parlamentar levam à lista de prestação de contas, quando
  a LOA tem norma, ou à de emendas, filtradas pela entidade e pelo parlamentar. Evidência:
  `_templates/v2018/loa/emendaloa_totalize_entidade.html:4-60`.

### Exclusão

- LOA-CRUD-064 [implementado] Excluir a LOA apaga os vínculos com parlamentares. A LOA com emenda
  ou outro registro que a referencie não é excluída: a tela volta com a mensagem "Registro não pode
  ser removido, pois é referenciado por outros registros" e a lista deles. Evidência:
  `cmj/loa/views/v_loa.py:270-275`, `sapl/crud/base.py:1058-1078`,
  `cmj/loa/models/m_emendaloa.py:197-199`.

### Emenda transformada em coletiva

- LOA-CRUD-065 [implementado] A emenda na fase -10 (transformada em coletiva) não entra em nenhum
  cálculo desta spec: já destinado e impedimento do resumo por parlamentar, impedimentos do
  recálculo das disponibilidades (LOA-CRUD-070) e escolha da LOA de `/loa/atual`. O manager padrão
  de `EmendaLoa` já esconde a fase -10 nas consultas que partem dela e nos acessos relacionados
  (`loa.emendaloa_set`, `agrupamento.emendas`), o que cobre os resumos por unidade e por entidade;
  as consultas que chegam à emenda por junção, a partir de outro model, filtram a fase
  explicitamente. Fora desta spec, o mesmo filtro vale na "Movimentação Geral" do PDF da listagem
  (LOA-LST-061), nas entidades e unidades do filtro da listagem (LOA-LST-030), nas entidades por LOA
  da API (LOA-PCL-083) e na lista de empenhos da LOA, que ainda não tem spec. Evidência:
  `cmj/loa/models/m_emendaloa.py:35-42`, `cmj/loa/views/v_loa.py:49-52`,
  `cmj/loa/services/s_loa.py:195-201`, `cmj/loa/services/s_loa.py:128-139`,
  `cmj/loa/views/v_financeiro_execucao.py:112-124`.

### Ativo e inativo pelo mandato

- LOA-CRUD-067 [implementado] No detalhe da LOA, ativo é o parlamentar com mandato, de titular ou de
  suplente, na legislatura de referência da LOA, e inativo é o que não tem. A legislatura de
  referência é a que contém o ano da LOA. A exceção é a LOA do primeiro ano de uma legislatura
  enquanto a RCL definitiva não é lançada (`rcl_previa` igual à RCL): até lá valem os parlamentares
  originais (LOA-CRUD-069); com a RCL definitiva, passam a valer os da legislatura do ano da LOA,
  que fazem os ajustes na execução. O campo `ativo` do cadastro não é consultado: quem ficou sem
  mandato numa legislatura pode voltar a ter em outra. A regra fica em
  `LoaService.parlamentares_com_mandato` e vale para a ordem das linhas, para a etiqueta e para
  LOA-CRUD-046. Evidência: `cmj/loa/services/s_loa.py:43-63`, `cmj/loa/services/s_loa.py:182-183`,
  `cmj/loa/services/s_loa.py:251-254`,
  `_templates/v2018/loa/widget_loaparlamentar_set_list.html:35`.
- LOA-CRUD-069 [implementado] Os parlamentares originais da LOA são os que têm mandato na
  legislatura do projeto, a do ano anterior ao da LOA. Só diferem dos da legislatura do ano da LOA
  na LOA do primeiro ano de uma legislatura. São eles que dividem a disponibilidade no "Valor por
  Parlamentar" (LOA-CRUD-039), antes e depois da RCL definitiva, mesmo quando a legislatura
  seguinte tem outro número de parlamentares. Evidência: `cmj/loa/services/s_loa.py:35-41`,
  `cmj/loa/services/s_loa.py:65-69`.

### Valor do ajuste

- LOA-CRUD-066 [implementado] O valor de cada parlamentar num registro de ajuste é maior ou igual a
  zero: o formulário de ajuste e a API recusam valor negativo. Evidência:
  `cmj/loa/forms/f_ajusteloa.py:77-88`, `cmj/loa/models/m_ajusteloa.py:264-270`.

## Riscos de segurança

Nenhum em aberto.

## Dúvidas

Informação do responsável, em 2026-11-24, que deu origem a LOA-CRUD-067, 069 e 070: a LOA do primeiro ano de uma legislatura (a de 2025, por exemplo) é um caso
particular. Os impedimentos das emendas dos parlamentares da legislatura anterior não podem ser
sanados por eles, e o valor fica disponível para ser dividido entre os parlamentares da nova
legislatura. Isso se repete a cada mudança de legislatura.

- D16. Pendência, adiada em 2026-11-25: fica para uma tarefa específica do CRUD genérico. O
  tratamento de `ProtectedError` do CRUD genérico fica em `delete()` (`sapl/crud/base.py:1058-1078`),
  que o Django 5.2 não chama no POST da exclusão. Toda tela CRUD que tente excluir um registro
  protegido termina em erro 500, exceto a da LOA (LOA-CRUD-064).

## Fora do escopo

- `LoaCrud.PrestacaoContaView` e o painel da prestação de contas: `prestacao-contas-tela.md`
  (`LOA-PCT`), `prestacao-contas-consulta.md` (`LOA-PCC`) e `prestacao-contas-painel.md` (`LOA-PCL`).
- Os `MasterDetailCrud` filhos da LOA (emendas, agrupamentos, ajustes, orçamento, execução e
  prestação de contas) e a API `/api/loa/loa/`.
- O conteúdo de `loa/despesas_espelho.html` e o bundle `loa` do v2018 que ele carrega.
- O mecanismo genérico do `Crud` além do que o detalhe da LOA usa.
