# LOA: consulta consolidada da prestação de contas

Status: implementado (2026-11-23)
Última verificação: 2026-11-23 (sobre o `master` `edd6cae51`)
Código principal: `cmj/loa/services/s_prestacaoconta.py`, `cmj/api/loa/views/prestacaoconta.py`,
`cmj/api/loa/views/loa.py`, `cmj/loa/views/v_loa.py`, `cmj/api/loa/serializers/__init__.py`
Testes: `cmj/loa/tests/test_prestacao_contas_consulta.py`

Leva ao backend os cálculos que hoje o painel do v2018 faz no navegador sobre a lista inteira de
emendas e ajustes de uma LOA: o valor de cada item, a totalização, a execução por empenhos e as
distribuições do dashboard. O comportamento atual do painel está em
[prestacao-contas-painel.md](./prestacao-contas-painel.md) (`LOA-PCL`), e o da tela e do relatório
em [prestacao-contas-tela.md](./prestacao-contas-tela.md) (`LOA-PCT`). Esta spec diz o que o
backend passa a responder; a troca do painel para usar essas respostas é etapa posterior.

## Escopo

- **App e serviço**: app `loa`, classe `PrestacaoContaService` em
  `cmj/loa/services/s_prestacaoconta.py`. Toda regra de valor, de totalização e de agrupamento fica
  nela. O serviço recebe o usuário, as LOAs e os filtros já validados; não lê `request`.
- **Pontos de entrada**, todos só de leitura: o relatório para impressão da tela (LOA-PCC-070) e
  quatro consultas em `loa/loa`:
  - `GET /api/loa/loa/<pk>/prestacaoconta_resumo/`: totalização e execução;
  - `GET /api/loa/loa/<pk>/prestacaoconta_dashboard/`: distribuições do dashboard;
  - `GET /api/loa/loa/<pk>/prestacaoconta_itens/`: lista de cartões, paginada pelo servidor.
  - `GET /api/loa/loa/<pk>/prestacaoconta_opcoes/`: opções dos seletores de filtro.
- **Legado tocado**: nenhum comportamento existente muda nesta etapa. As rotas `loa/emendaloa`,
  `loa/registroajusteloa` e os `totalize_empenhos` continuam como estão, e o painel continua a
  usá-las até a troca. São reaproveitados `EmendaLoaFilterSet` e `RegistroAjusteLoaFilterSet`
  (`cmj/api/forms.py`) e `VisibilidadeLoaService` (`cmj/loa/services/s_visibilidade.py`).

Dados de referência (executado em 2026-11-23, banco de desenvolvimento): a LOA 2026 tem 385 emendas,
112 registros de ajuste e 513 vínculos de empenho; dos 290 ajustes da base, 10 se referem a mais de
uma emenda e 2 têm mais de um parlamentar.

Conferência com a tela atual (executado em 2026-11-23, banco de desenvolvimento, como anônimo e em
somente leitura): as fórmulas do painel, transcritas do JavaScript e aplicadas às respostas das
rotas atuais, foram comparadas com as consultas novas em 220 combinações de exercício e filtro (LOAs
de 2023 a 2026; situação, tipos, ajustes, cada parlamentar, unidades, entidades, busca e vários
exercícios juntos). Totais, contagens e todas as distribuições do dashboard coincidiram nas 220. A
única diferença, em 28 delas, é a esperada: a execução de 2023 a 2025, onde o empenho ligado a
emenda e a ajuste deixa de contar duas vezes (LOA-PCC-021); em 2026 não há diferença. Os 1.033
cartões das quatro LOAs trazem os mesmos valores, parlamentares, unidade, entidade e objeto das
rotas atuais; as emendas, na mesma ordem, e os ajustes, pela numeração (LOA-PCC-040). Custo medido
na LOA 2026 (497 itens): resumo, 9 a 14 consultas ao banco; dashboard, 11; página de 40 cartões, 7 a
10, contra 608 por página de emendas e 1.152 por página de ajustes nas rotas atuais (LOA-PCL-081).

## Regras

### Entrada e filtros

- LOA-PCC-001 [implementado] As três consultas recebem os mesmos filtros que o painel envia hoje à
  busca (LOA-PCL-033): `situacao`, `unidade`, `entidade`, `search`, `tipo__in` e `parlamentar`.
  Emendas e ajustes são filtrados pelos filtersets que a API já usa, de modo que um mesmo filtro
  seleciona os mesmos registros na consulta nova e nas rotas atuais. Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:134-160`,
  `cmj/loa/services/s_prestacaoconta.py:176-187`.
- LOA-PCC-002 [implementado] O parâmetro `ajustes` e a presença de `tipo__in` decidem o que entra,
  como hoje (LOA-PCL-030): sem `tipo__in` e sem `ajustes=True`, emendas e ajustes; só com
  `tipo__in`, emendas; só com `ajustes=True`, ajustes; com os dois, emendas e ajustes, ambos
  restritos aos tipos pedidos. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:128-132`.
- LOA-PCC-003 [implementado] O parâmetro `loas` acrescenta outros exercícios ao da rota (ids
  separados
  por vírgula). As consultas respondem sobre o conjunto dos exercícios pedidos, numa conta só. Um
  exercício extra obedece às mesmas condições da LOA da rota (LOA-PCT-064): visível ao usuário e
  com norma. Aceito em 2026-11-23: hoje os botões de exercício do painel oferecem toda LOA de 2023
  em diante, e a publicada sem norma entra na prestação de contas com as emendas ainda em proposta
  (LOA-PCL-019 e 076). Evidência: `cmj/loa/services/s_prestacaoconta.py:110-126`.
- LOA-PCC-004 [implementado] Filtro com valor inválido (id que não é número, tipo inexistente)
  responde
  400 com a mensagem do campo; nunca 500. Aceito em 2026-11-23. Evidência:
  `cmj/api/loa/views/prestacaoconta.py:10-46`,
  `cmj/loa/services/s_prestacaoconta.py:176-187`.
- LOA-PCC-005 [implementado] Dois cortes por ano são regra e ficam no serviço, como constantes
  nomeadas, e em nenhum outro lugar: a prestação de contas vale para exercícios de 2023 em diante,
  e os totais de execução, de 2026 em diante. A LOA da rota anterior a 2023 responde 404 nas
  consultas. Aceito em 2026-11-23: hoje os dois anos estão fixos no código do painel.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:69-72`,
  `cmj/loa/services/s_prestacaoconta.py:96-104`.

### Valor de cada item

- LOA-PCC-010 [implementado] O valor final de uma emenda é zero quando ela tem ao menos um registro
  de
  ajuste ou está em impedimento técnico (fase 40); nos demais casos é o valor original. O valor
  remanejado é contado no registro de ajuste, que entra na lista como item próprio: assim a soma
  fecha sem contar duas vezes, inclusive nos ajustes sem emenda e nos de várias emendas. Aceito em
  2026-11-23; é o que `EmendaLoa.valor_computado` já faz. O trecho desse método que somaria os
  ajustes, depois do `return`, saiu do model. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:226-235`,
  `cmj/loa/services/s_prestacaoconta.py:309-313`,
  `cmj/loa/models/m_emendaloa.py:636-647`.
- LOA-PCC-011 [implementado] O valor de um registro de ajuste é a soma das partes por parlamentar;
  em
  impedimento (fase 40) é zero. É o que `RegistroAjusteLoa.valor_computado` faz hoje. Um ajuste
  ligado a várias emendas conta uma vez, pelo próprio valor. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:280-285`,
  `cmj/loa/services/s_prestacaoconta.py:302-307`.
- LOA-PCC-012 [implementado] Com filtro de parlamentar, o valor do item passa a ser a parte desse
  parlamentar: no ajuste, a parte dele (zero se o ajuste está em impedimento); na emenda sem ajuste
  e fora de impedimento, a parte dele no valor original. A emenda com ajuste ou em impedimento
  continua valendo zero. É o `valorEfetivo` do painel (LOA-PCL-064). Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:236-239`,
  `cmj/loa/services/s_prestacaoconta.py:285`.
- LOA-PCC-013 [implementado] O valor atribuído a um parlamentar nas distribuições é: no ajuste, a
  parte
  dele; na emenda sem ajuste e fora de impedimento, a parte dele no valor original; na emenda com
  ajuste ou em impedimento, zero. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:232-239`,
  `cmj/loa/services/s_prestacaoconta.py:283-284`.

### Resumo

- LOA-PCC-020 [implementado] O resumo devolve, para os itens selecionados: a quantidade total de
  itens
  da seleção e, para "Impositivas" (tipos 10 e 99), "Saúde" (10), "Áreas Diversas" (99) e
  "Modificativas" (0), a soma dos valores (LOA-PCC-010 a 012) e a contagem de cada grupo. A
  contagem de "Impositivas" é a das impositivas, e não a da lista inteira. Aceito em 2026-11-23:
  corrige a contagem que o painel mostrava ao lado de "Total Impositivas", que incluía as
  modificativas (hoje LOA-PCL-090). Evidência: `cmj/loa/services/s_prestacaoconta.py:321-326`,
  `cmj/loa/services/s_prestacaoconta.py:348-355`.
- LOA-PCC-021 [implementado] O resumo devolve os quatro totais de execução (empenhado, liquidado,
  pago
  bruto e anulado) dos empenhos ligados aos itens selecionados, e cada empenho conta uma vez: o
  que está ligado a uma emenda e a um ajuste, ou a itens de dois exercícios, não é somado de novo.
  Aceito em 2026-11-23; é a regra que a aba Empenhos do cartão já segue (LOA-PCL-051).
  (executado) Na LOA 2025 seis empenhos estão ligados a emenda e a ajuste, e a soma por resposta
  dá 452.080,30 a mais; na LOA 2026 não há sobreposição. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:362-376`.
- LOA-PCC-022 [implementado] O resumo informa se os totais de execução valem para o conjunto pedido:
  valem quando todos os exercícios são do ano inicial da execução em diante (LOA-PCC-005). Os
  totais são devolvidos de qualquer forma; exibir ou avisar é do painel. Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:377-381`.
- LOA-PCC-024 [implementado] O resumo devolve os exercícios disponíveis para o usuário (id e ano):
  as
  LOAs que ele vê, com norma, do ano inicial da prestação de contas em diante. É dessa lista que
  o painel passa a montar os botões de exercício. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:96-104`,
  `cmj/loa/services/s_prestacaoconta.py:339-347`.
- LOA-PCC-023 [implementado] O total é sempre a soma dos itens selecionados: com o filtro só de
  emendas,
  as que têm ajuste continuam contadas com valor zero (LOA-PCC-010) e os ajustes delas não entram.
  Para o painel poder avisar, o resumo devolve à parte a quantidade e a soma do valor original das
  emendas selecionadas que valem zero por terem registro de ajuste, e o mesmo para as que valem
  zero só por impedimento. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:328-335`,
  `cmj/loa/services/s_prestacaoconta.py:356-358`.

### Dashboard

- LOA-PCC-030 [implementado] "Situação" por tipo (10 e 99): emendas e ajustes do tipo agrupados pela
  situação, com rótulo, contagem, soma dos valores e a distribuição por parlamentar (LOA-PCC-013),
  do grupo com mais itens para o com menos. Como hoje (LOA-PCL-068), "Impedimento" (40), "Em
  Execução" (60) e "Finalizada" (99) reúnem emendas e ajustes; as demais fases da emenda ficam com
  o rótulo da própria fase, e o ajuste registrado (10), com "Registrado". Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:444-488`.
- LOA-PCC-031 [implementado] "Por parlamentar em Áreas Diversas": só itens do tipo 99; por
  parlamentar,
  o total, as contagens de emendas e de ajustes e a divisão por unidade orçamentária, do maior
  total para o menor. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:490-524`.
- LOA-PCC-032 [implementado] "Por unidade orçamentária": só itens do tipo 99 com unidade; total,
  contagem e distribuição por parlamentar, do maior total para o menor. Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:526-553`.
- LOA-PCC-033 [implementado] "Por entidade": só emendas impositivas com entidade; total, contagem e
  distribuição por parlamentar, do maior total para o menor. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:544-560`.
- LOA-PCC-034 [implementado] O dashboard devolve as listas inteiras, ordenadas; o corte nas dez
  maiores e as barras proporcionais são apresentação e ficam no painel. Aceito em 2026-11-23.
  Evidência: `cmj/loa/services/s_prestacaoconta.py:549-560`.

### Itens

- LOA-PCC-040 [implementado] A lista de itens traz as emendas seguidas dos ajustes, por exercício do
  mais recente para o mais antigo; emendas por sigla do tipo e número da matéria, ajustes pela
  numeração do registro (LOA-PCC-044). A paginação é do servidor, com `page` e `page_size` (até
  100). Aceito em 2026-11-23. Evidência: `cmj/loa/services/s_prestacaoconta.py:563-617`.
- LOA-PCC-041 [implementado] Cada item traz o que o cartão mostra (LOA-PCL-046 a 048, 053 e 054):
  identificação e link, tipo, fase com rótulo, valores original e final, parlamentares com
  fotografia e parte, unidade, entidade, objeto e, no ajuste, as emendas vinculadas só com id e
  título. Aceito em 2026-11-23. Evidência: `cmj/loa/services/s_prestacaoconta.py:869-954`,
  `cmj/loa/services/s_prestacaoconta.py:956-1028`.
- LOA-PCC-042 [implementado] O rótulo da fase vem do backend, das escolhas do próprio model: a do
  ajuste finalizado é "Finalizado" (fase 99). Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:932-933`,
  `cmj/loa/services/s_prestacaoconta.py:1012`.
- LOA-PCC-043 [implementado] Cada item traz as contagens do que as abas do cartão mostram: registros
  de prestação de contas, ajustes vinculados (na emenda), vínculos de empenho (na emenda, os dela
  mais os dos ajustes dela) e, havendo matéria, tramitações e documentos acessórios. Com elas o
  cartão
  decide quais abas existem e a ordem (LOA-PCL-049 e 055) sem requisição. O conteúdo das abas
  continua nas rotas atuais nesta etapa. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:898-916`,
  `cmj/loa/services/s_prestacaoconta.py:946-952`, `cmj/loa/services/s_prestacaoconta.py:1023-1026`.
- LOA-PCC-044 [implementado] Toda listagem de registros de ajuste sai pela numeração do registro, ano
  e número do RAT, qualquer que seja o parlamentar: é a ordem padrão do model, que telas e
  relatórios herdam, a do filtro da API, que vale nas rotas atuais mesmo quando o cliente pede outra
  ordem, e a da lista de itens. Aceito em 2026-11-23: os campos `numero` e `ano` são recentes, e os
  pontos que definem a sequência continuavam pelo id, a ordem de cadastro. (executado) Os 290
  ajustes da base têm número e ano, sem pares repetidos; a numeração foi atribuída por exercício e
  por ofício de ajuste, de modo que em 2026 as duas ordens coincidem e em 2023, 2024 e 2025 os
  ajustes passam a sair agrupados por ofício. Evidência: `cmj/loa/models/m_ajusteloa.py:179-180`,
  `cmj/api/forms.py:144-150`, `cmj/loa/services/s_prestacaoconta.py:573-576`.

### Opções dos filtros

- LOA-PCC-090 [implementado] `GET /api/loa/loa/<pk>/prestacaoconta_opcoes/` devolve as opções dos
  seletores de filtro para os exercícios pedidos (a LOA da rota e os de `loas`; os demais filtros
  não contam): os parlamentares das LOAs, por nome; as unidades orçamentárias que recebem emenda
  impositiva, com o ano, por exercício e código; e as entidades ativas com emenda ou registro de
  ajuste nesses exercícios, por nome, com o rótulo que o seletor mostra. Vale o mesmo acesso das
  outras consultas (LOA-PCC-060), e o custo no banco é fixo. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:622-666`, `cmj/api/loa/views/prestacaoconta.py:94-96`.

### Relatório

- LOA-PCC-070 [implementado] O relatório para impressão (`/loa/<pk>/prestacaoconta?print=True`,
  LOA-PCT) pede os itens ao mesmo serviço: a mesma seleção das consultas (filtros, tipos, ajustes e
  exercícios extras), emendas e ajustes na ordem da lista (LOA-PCC-040) e os valores decididos pelas
  mesmas regras (LOA-PCC-010 e 011). O serviço entrega cada item com tudo o que o relatório imprime
  (parlamentares, prestação de contas e arquivos, empenhos, ajustes, registros contábeis,
  tramitações e documentos acessórios) em número fixo de consultas, qualquer que seja a quantidade
  de itens. A emenda que vale zero sai marcada com o motivo, ajuste ou impedimento. Aceito em
  2026-11-23, com o plano de levar o relatório ao serviço. O texto dos registros contábeis vem de
  uma view do banco que não existe nos testes: esse trecho foi conferido só na base de
  desenvolvimento. Evidência: `cmj/loa/services/s_prestacaoconta.py:670-803`,
  `cmj/loa/views/v_loa.py:931-972`.

### Rotas de emendas e de ajustes

- LOA-PCC-080 [implementado] As rotas `loa/emendaloa` e `loa/registroajusteloa`, que continuam
  servindo às abas dos cartões, às telas de edição e ao dashboard da LOA no v6, têm custo no banco
  que não cresce com a quantidade de itens: o queryset de cada uma carrega de uma vez o que o
  serializer lê (relações, partes por parlamentar, empenhos, existência e contagem de ajustes), e as
  quatro somas de empenhos de um item saem de um cálculo só. A resposta não muda. Aceito em
  2026-11-23. (executado) O JSON de 100 pedidos às duas rotas, em todas as LOAs, com e sem `expand`,
  ficou idêntico, e o custo deles caiu de 52.383 para 1.774 consultas; a página de 100 emendas foi
  de 1.313 consultas para 7, a de 100 ajustes de 1.321 para 12, e as 907 emendas de uma vez, de
  12.587 consultas e 8,7 s para 7 e 0,7 s. Com `expand`, cada objeto expandido ainda custa as
  consultas do mecanismo genérico (API-SER-026). Evidência:
  `cmj/api/loa/serializers/__init__.py:23-75`, `cmj/api/loa/serializers/__init__.py:77-97`,
  `cmj/api/loa/views/emendaloa.py:61-67`, `cmj/api/loa/views/registroajusteloa.py:13-14`,
  `cmj/loa/models/m_emendaloa.py:637-647`.

### Formato

- LOA-PCC-050 [implementado] Valores monetários saem como texto decimal com duas casas
  (`"1234.56"`),
  sem formatação regional; formatar é do painel. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:25-28`.

## Requisitos de segurança

- LOA-PCC-060 [implementado] As três consultas são públicas e só de leitura (`GET`), como a tela. A
  LOA da rota segue a visibilidade da LOA (API-ACS-051): a que o usuário não vê responde 404. Um
  id em `loas` que não esteja entre os exercícios disponíveis (LOA-PCC-024), por não existir, não
  ser visível ou não ter norma, responde 400, sem distinguir o motivo. Aceito em 2026-11-23. Itens
  da varredura: 1. Evidência: `cmj/api/loa/views/loa.py:77-85`,
  `cmj/api/loa/views/prestacaoconta.py:55-58`, `cmj/loa/services/s_prestacaoconta.py:110-122`.
- LOA-PCC-061 [implementado] As respostas trazem só o que os cartões e o dashboard mostram. Não saem
  `owner`, `metadata`, `search` nem campos de auditoria; do parlamentar, só id, nome e fotografia.
  Itens da varredura: 2. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:918-953`,
  `cmj/loa/services/s_prestacaoconta.py:1000-1027`.
- LOA-PCC-062 [implementado] O custo no banco não depende da quantidade de itens: resumo e dashboard
  fazem um número fixo de consultas, e a lista de itens, um número fixo por página. Um teste fixa
  esses números. Itens da varredura: 7. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:191-193`,
  `cmj/loa/services/s_prestacaoconta.py:805-818`,
  `cmj/loa/tests/test_prestacao_contas_consulta.py:313`.
- LOA-PCC-063 [implementado] `loas` aceita no máximo 10 ids; acima disso a resposta é 400. Itens da
  varredura: 7. Aceito em 2026-11-23. Evidência: `cmj/loa/services/s_prestacaoconta.py:115-119`.
- LOA-PCC-064 [implementado] O `search` vai ao banco só como parâmetro do filterset, sem SQL montado
  à
  mão. Itens da varredura: 4. Aceito em 2026-11-23. Evidência:
  `cmj/loa/services/s_prestacaoconta.py:176-187`.

Itens sem requisito: 3 (não serve arquivo; os links de arquivo continuam nas rotas atuais), 5 (sem
cache, índice ou log próprios nesta etapa) e 6 (sem configuração nova).

## Riscos de segurança

Nenhum risco encontrado no legado alcançado nos itens 1 a 7 (2026-11-23).

## Dúvidas

- D1. Resolvida em 2026-11-23: LOA-PCC-010.
- D2. Resolvida em 2026-11-23: LOA-PCC-023.
- D3. Resolvida em 2026-11-23: LOA-PCC-021.
- D4. Resolvida em 2026-11-23: LOA-PCC-020.
- D5. Resolvida em 2026-11-23: LOA-PCC-003, 024 e 060.
- D6. Resolvida em 2026-11-23: LOA-PCC-005 e 022.
- D7. Resolvida em 2026-11-23: LOA-PCC-043; o conteúdo das abas fica para etapa própria.

## Fora do escopo

- A troca do painel do v2018 para usar estas consultas, bloco a bloco, e a remoção dos cálculos do
  navegador, que fica registrada na spec do painel: a totalização, o dashboard e a lista de
  cartões já usam estas consultas (LOA-PCL-089 a 102).
- A cópia do painel no v6 (`_frontend/v6/src/modules/loa/pcl/`), que fica como está.
- O conteúdo das abas dos cartões numa consulta única por item, com os empenhos da emenda e dos
  ajustes dela reunidos no servidor (dúvida D14 do painel). É a etapa seguinte à troca do resumo,
  do dashboard e da lista.
- Gravação: registro de prestação de contas, ajustes e vínculo de empenhos continuam nas telas e
  rotas atuais.
