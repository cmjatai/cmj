# API: paginação, `get_all` e custo das rotas geradas

Status: observado, com API-CUS-020 e 022 implementadas (acordadas em 2026-11-21 e 22, com teste) e
API-CUS-024 e 025 acordadas
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `sapl/api/pagination.py`, `cmj/settings/drf.py`, `drfautoapi/drfautoapi.py`,
`sapl/api/urls.py`, `sapl/api/views_schema.py`, `docker/start_gunicorn.sh`
Testes: `sapl/api/tests/test_api_paginacao.py`, `sapl/api/tests/test_api_esquema.py`

Como as listas são paginadas, o que `get_all` muda, quanto custa cada caminho genérico (consultas,
tempo e tamanho) e quem, nos três frontends e nos templates, depende de `get_all`.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste. As medições são de 2026-11-21, no banco de desenvolvimento, como anônimo, com
`django.test.Client` nas rotas reais, só com `GET`, a sessão do banco em somente leitura e um
contador próprio de consultas. Valem para um processo só, na máquina de desenvolvimento, sem
cache (`DummyCache`) e sem concorrência: servem para comparar caminhos, e não como tempo de
produção. O levantamento dos frontends foi feito por busca no código, com as linhas conferidas por
amostragem; o JavaScript não foi executado.

## Escopo

`StandardPagination`, o parâmetro `get_all`, a ausência de limite de requisições, o custo por
requisição e por item das rotas geradas, o custo de `expand`, de filtros e do esquema OpenAPI, e o
levantamento de quem chama a API com `get_all`. Os serializers próprios da LOA entram só como
comparação.

## Regras

### Paginação

- API-CUS-001 [observado] As listas usam `StandardPagination`: 10 itens por página, tamanho
  ajustável pelo parâmetro `page_size` até o teto de 100. (executado) `page_size=1000` devolve 100
  itens, e página inexistente responde 404. Evidência: `sapl/api/pagination.py:8-11`,
  `cmj/settings/drf.py:23`.
- API-CUS-002 [observado] A resposta paginada tem `pagination` (links, página anterior e seguinte,
  índices, `total_entries`, `total_pages` e `page`) e `results`. Evidência:
  `sapl/api/pagination.py:115-139`.
- API-CUS-003 [observado] `get_all=true`, com qualquer caixa, desliga a paginação: a resposta é a
  lista inteira, sem envelope, dentro do teto de API-CUS-020. (executado) `get_all=1` não tem
  efeito. Evidência: `sapl/api/pagination.py:13-17`.
- API-CUS-020 [implementado] Com `get_all`, a lista inteira só sai se tiver até
  `API_GET_ALL_MAX_ITEMS` itens (2.000 por padrão, configurável por variável de ambiente). Acima
  disso a resposta é 400, com a chave `get_all` pedindo filtro ou paginação. Fica sem teto quem
  tem a permissão `list_` do model listado; anônimo e conta sem essa permissão, inclusive a criada
  por login social, ficam com o teto. A contagem para até o teto, sem percorrer a tabela. Evidência:
  `sapl/api/pagination.py:19-46`, `cmj/settings/drf.py:37-39`.
- API-CUS-021 [observado] (executado) Os maiores pedidos de `get_all` dos frontends hoje: 819 itens
  no dashboard da LOA (emendas de todas as LOAs com orçamento impositivo de uma vez) e 415 na ordem
  do dia de uma sessão, em telas públicas; e 21.232 documentos de uma classe em `arq/arqdoc`, na
  tela de administração do arquivo, restrita ao grupo "Operador do Modulo Arq", que tem a
  permissão `list_arqdoc`. Evidência:
  `_frontend/v6/src/modules/loa/dashboard/LoaDashboard.vue:142-153`,
  `_frontend/v6/src/modules/sessao/SessaoPlenariaView.vue:122`,
  `_frontend/v6/src/modules/arq/admin/DocListLayout.vue:110`.
- API-CUS-004 [observado] `get_all` vale também nas actions que devolvem lista pelo mesmo
  paginador. (executado) `norma/normajuridica/destaques/?get_all=true` devolve os 17 itens.
  Evidência: `sapl/api/pagination.py:13-17`, `drfautoapi/drfautoapi.py:605-610`.
- API-CUS-005 [observado] A aplicação não limita o número de requisições (throttling) em nenhuma
  rota gerada: as settings do DRF não declaram classes de throttle, e o limite por IP existente
  cobre só o login. O nginx do container também não limita `/api`. Evidência:
  `cmj/settings/drf.py:3-32`, `cmj/api/views.py:117-120`, `docker/nginx/cmj_docker.conf:114-116`.
- API-CUS-024 [acordado] O limite de requisições por IP das rotas `/api` fica no proxy da frente, o
  nginx do host, e não na aplicação: ele vê o IP do cliente, atua antes de a requisição chegar aos
  containers e vale para todos eles. A aplicação não usa o throttling do DRF. A taxa é escolhida a
  partir do tráfego medido, para não atingir as telas que fazem muitas requisições por página,
  como a da sessão plenária e o painel. Evidência: `cmj/settings/drf.py:3-32`,
  `docker/nginx/cmj_docker.conf:17-26`.

### Custo por requisição e por item

- API-CUS-006 [observado] (executado) Toda lista gerada faz 4 consultas fixas: configuração da casa,
  a da resposta condicional (API-GER-033), a contagem total e a página. A rota com visibilidade
  por registro e a requisição com `expand` não fazem a da resposta condicional (API-GER-034).
  Evidência: `sapl/api/views.py:115-132`, `sapl/api/pagination.py:13-17`.
- API-CUS-025 [acordado] A contagem total de cada lista e a montagem da resposta de `get_all` na
  memória ficam como estão, por decisão de 2026-11-22: a contagem é o que permite a paginação
  com total, a resposta condicional custa uma consulta (API-GER-033) e o `get_all` tem o teto de
  API-CUS-020. Evidência: `sapl/api/pagination.py:13-17`, `sapl/api/pagination.py:19-45`.
- API-CUS-007 [observado] O viewset gerado consulta `Model.objects.all()`, sem `select_related` nem
  `prefetch_related`. Evidência: `drfautoapi/drfautoapi.py:539`.
- API-CUS-008 [observado] (executado) As consultas por item do caminho genérico vêm do campo
  `__str__`: o `__str__` do model lê objetos relacionados, uma consulta para cada um. Em
  `materia/tramitacao`, a página de 100 faz 305 consultas, e a mesma página com
  `exclude=__str__` faz 5. Evidência: `drfautoapi/drfautoapi.py:694-695`.
- API-CUS-009 [observado] (executado) Consultas por página de 100 itens, sem `expand`, conforme a
  tabela. Evidência: `drfautoapi/drfautoapi.py:539`, `drfautoapi/drfautoapi.py:694-695`.

| Rota | Linhas na tabela | Consultas | Por item | Tempo | Resposta |
| --- | --- | --- | --- | --- | --- |
| `parlamentares/parlamentar` | 172 | 5 | 0 | 59 ms | 266 kB |
| `loa/empenho` | 117.327 | 105 | 1 | 79 ms | 228 kB |
| `materia/tramitacao` | 75.196 | 305 | 3 | 187 ms | 54 kB |
| `sessao/sessaoplenaria` | 1.313 | 305 | 3 | 399 ms | 178 kB |
| `norma/normajuridica` | 7.928 | 305 | 3 | 201 ms | 194 kB |
| `materia/autoria` | 30.084 | 405 | 4 | 204 ms | 21 kB |
| `sessao/ordemdia` | 17.180 | 605 | 6 | 263 ms | 56 kB |
| `materia/materialegislativa` | 23.596 | 804 | 8 | 692 ms | 346 kB |
| `sessao/registrovotacao` | 14.574 | 1.105 | 11 | 546 ms | 61 kB |
| `loa/emendaloa` (serializer próprio) | 907 | 7 | 0,1 | 93 ms | 217 kB |
| `loa/registroajusteloa` (serializer próprio) | 290 | 12 | 0,1 | 275 ms | 244 kB |

- API-CUS-010 [observado] (executado) As listas do gerador puro custam de 0 a 11 consultas por item.
  As duas da LOA com serializer próprio, `loa/emendaloa` e `loa/registroajusteloa`, custavam 13 por
  item e, desde 2026-11-23, têm custo fixo por página, porque o queryset carrega de uma vez o que o
  serializer lê (LOA-PCC-080); as linhas delas na tabela são dessa data. Evidência:
  `cmj/api/loa/serializers/__init__.py:23-75`, `drfautoapi/drfautoapi.py:694-695`.

### `get_all` medido

- API-CUS-011 [observado] (executado) Uma requisição com `get_all=true` custa o que a tabela
  mostra. As medições são anteriores ao teto de API-CUS-020: hoje as respostas acima de 2.000
  itens só saem para quem tem a permissão `list_` do model, e os demais recebem 400 em menos de
  1 s. A coluna de memória é o aumento do pico do processo durante a chamada, com as
  chamadas feitas em sequência na ordem em que o pico cresceu. A resposta é montada inteira na
  memória antes de sair. Não foram medidas `compilacao/dispositivo` (160 mil linhas) nem
  `materia/analisesimilaridade` (600 mil), também públicas. Evidência:
  `sapl/api/pagination.py:13-17`.

| Rota | Itens | Consultas | Tempo | Resposta | Memória do processo |
| --- | --- | --- | --- | --- | --- |
| `parlamentares/parlamentar` | 172 | 4 | 0,06 s | 0,4 MB | sem aumento |
| `sessao/sessaoplenaria` | 1.313 | 4.128 | 2,0 s | 2,2 MB | sem aumento |
| `loa/emendaloa` (em 2026-11-23, LOA-PCC-080) | 907 | 7 | 0,7 s | 1,5 MB | não medido |
| `norma/normajuridica` | 7.928 | 23.788 | 13,5 s | 14,6 MB | +84 MB |
| `materia/autoria` | 30.084 | 117.686 | 59 s | 6,5 MB | +164 MB |
| `loa/empenho` | 117.327 | 117.331 | 69 s | 294 MB | +1.523 MB |
| `sessao/registrovotacao` | 14.574 | 158.191 | 75 s | 9,0 MB | +441 MB |
| `materia/tramitacao` | 75.196 | 225.592 | 114 s | 41,1 MB | +165 MB |
| `materia/materialegislativa` | 23.596 | 168.681 | 135 s | 65,6 MB | +539 MB |

- API-CUS-012 [observado] Em produção, o gunicorn sobe 16 processos com tempo limite de 300 s, e o
  nginx espera a aplicação por até 600 s. Evidência: `docker/start_gunicorn.sh:7-9`,
  `docker/nginx/cmj_docker.conf:180-181`.

### `expand`, filtros e esquema

- API-CUS-013 [observado] (executado) `expand` acrescenta consultas por item para cada relação
  expandida e para o `__str__` de cada objeto expandido. A tabela mostra páginas de 100 itens.
  Quando o viewset do model expandido restringe o queryset, há mais uma consulta por objeto
  distinto (API-SER-026): 21 numa página de 40 ajustes da LOA com `expand=emendaloa`. Nas rotas da
  tabela o número de consultas não mudou com essa conferência. Evidência:
  `drfautoapi/drfautoapi.py:832-868`, `drfautoapi/drfautoapi.py:683`.

| Requisição | Consultas | Tempo | Resposta |
| --- | --- | --- | --- |
| `materia/tramitacao` sem `expand` | 305 | 0,2 s | 54 kB |
| `materia/tramitacao`, `expand=materia` | 1.005 | 1,0 s | 399 kB |
| `materia/tramitacao`, 4 caminhos | 2.030 | 1,3 s | 558 kB |
| `sessao/ordemdia`, `expand` usado pelo v6 | 1.521 | 1,0 s | 349 kB |
| `sessao/registrovotacao`, 3 caminhos de 3 níveis | 2.790 | 2,1 s | 900 kB |
| `sessao/sessaoplenaria`, `get_all` com 3 caminhos | 4.144 | 1,8 s | 3,2 MB |

- API-CUS-014 [observado] (executado) Filtros e ordenação sobre colunas sem índice, em página de 1
  item: `texto__icontains` em `compilacao/dispositivo` (160 mil linhas) leva de 0,2 a 0,5 s;
  `texto__iregex`, 0,2 s; `o=?` em `materia/analisesimilaridade` (600 mil linhas), 0,2 s; a última
  página de `materia/tramitacao`, 0,1 s. Evidência: `drfautoapi/drfautoapi.py:163-168`,
  `drfautoapi/drfautoapi.py:182-227`.
- API-CUS-015 [retirada] Substituída por API-CUS-022.
- API-CUS-022 [implementado] `GET /api/schema/` guarda no cache, por uma hora, a resposta já
  convertida, uma por formato e idioma. Enquanto ela está no cache, o esquema não é gerado nem
  convertido de novo, para nenhum usuário. Os parâmetros `version` e `lang` com valor que não muda
  o esquema não criam outra cópia. Evidência: `sapl/api/views_schema.py:7-56`,
  `sapl/api/urls.py:35`.
- API-CUS-023 [observado] (executado) Sem cache, o esquema custa 10 s e 10,4 MB em YAML, o formato
  padrão: 2,1 s para gerar e 8,0 s para converter; em JSON, 1,7 s e 22,1 MB. Com cache, a resposta
  seguinte sai em menos de 0,01 s. Em `DEBUG` o cache é `DummyCache`, e o esquema é gerado a cada
  requisição. Evidência: `sapl/api/views_schema.py:17-33`.

### Quem usa `get_all`

- API-CUS-016 [observado] `get_all` é enviado em 43 pontos dos frontends (31 no v6 e 12 no v2018) e
  em 5 templates. Há mais 4 ocorrências em arquivos `* copy.vue` do v6 e 1 comentada no v2018. O v8
  não usa, e nenhum código Python chama a API com ele. Evidência:
  `_frontend/v6/src/modules/sessao/SessaoPlenariaView.vue:122`,
  `_frontend/v2018/src/modules/loa/pcl/PclDetalheEmenda.vue:403`,
  `_templates/v2018/materia/autoria_form.html:17-18`.

| Onde | Usos | Rotas chamadas com `get_all` | Tela |
| --- | --- | --- | --- |
| v6, sessão plenária (`SessaoPlenariaView.vue`) | 13 | 9 de `sessao`, `materia/materialegislativa`, `materia/documentoacessorio`, `norma/legislacaocitada` | pública |
| v6, prestação de contas da LOA (`pcl/`) | 7 | `loa/prestacaocontaregistro`, `loa/registroajusteloa`, `loa/unidadeorcamentaria`, `loa/entidade`, `materia/documentoacessorio`, `materia/tramitacao` | pública |
| v6, dashboard da LOA | 2 | `loa/emendaloa`, `loa/loa` | pública |
| v6, painel (`painelset`) | 2 | `painelset/widget` | pública |
| v6, normas em destaque | 1 | `norma/normajuridica/destaques` | pública |
| v6, arquivo e draft | 6 | `arq/draft`, `arq/arqdoc`, `arq/arqclasse` | restrita |
| v6, arquivos `* copy.vue` | 4 | `loa/entidade`, `loa/unidadeorcamentaria`, `loa/loa` | código sem uso aparente |
| v2018, prestação de contas da LOA (`pcl/`, conteúdo das abas dos cartões) | 7 | `loa/prestacaocontaregistro`, `loa/registroajusteloa`, `loa/empenhoemendaajuste`, `materia/documentoacessorio`, `materia/tramitacao` | pública |
| v2018, edição de emenda, agrupamento e empenho | 5 | `loa/emendaloaregistrocontabil`, `loa/agrupamentoregistrocontabil`, `loa/agrupamento/<pk>/emendas`, `loa/emendaloa/search`, `loa/empenhoemendaajuste` | restrita |
| templates de autoria e protocolo | 5 | `base/autor/possiveis` | restrita |

- API-CUS-017 [observado] Em 39 dos 43 usos, a requisição leva um filtro que restringe o resultado
  a um registro pai ou a um conjunto de ids (uma sessão, uma emenda, uma LOA, uma matéria, um nó).
  Os outros 4 pedem a tabela inteira ou quase: `sessao/tiporesultadovotacao`, `loa/loa` (no v6, sem
  filtro), a action de normas em destaque e `arq/draft`, que o servidor restringe ao dono. São tabelas pequenas. O maior resultado esperado é o do dashboard da
  LOA, que pede as emendas de todas as LOAs carregadas. Evidência:
  `_frontend/v6/src/modules/sessao/SessaoPlenariaView.vue:252`,
  `_frontend/v6/src/modules/loa/dashboard/LoaDashboard.vue:149`,
  `_frontend/v6/src/modules/loa/dashboard/LoaDashboard.vue:171`.
- API-CUS-018 [observado] Os três frontends têm um `fetchSync` que, sem `get_all`, percorre todas
  as páginas seguindo `pagination.next_page`, a menos que receba `only_first_page`. Com isso, uma
  lista grande sem `get_all` vira uma requisição por página. O painel de prestação de contas do
  v2018, que tinha um laço próprio para isso, pede uma página por vez à consulta consolidada
  (LOA-PCL-099). Evidência: `_frontend/v6/src/stores/SyncStore.js:198-199`,
  `_frontend/v2018/src/stores/sync/sync.js:67-68`.
- API-CUS-019 [observado] O maior `page_size` pedido pelos frontends é 100, o teto do servidor.
  Evidência: `_frontend/v6/src/modules/loa/pcl/PclFiltros.vue:111`,
  `sapl/api/pagination.py:11`.

## Riscos de segurança

Varredura de 2026-11-21, item 7 de `docs/specs/README.md` (custo sem limite), sobre os caminhos
genéricos, revista em 2026-11-22.

Nenhum risco encontrado no item 7 (2026-11-22).

## Dúvidas

Nenhuma dúvida em aberto.

## Pendências encontradas

Pontos de eficiência medidos e deixados como estão por decisão de 2026-11-22. Não bloqueiam nada.

- P1. **O `__str__` custa consultas por item.** O `__str__` de vários models lê objetos
  relacionados, e uma página de 100 itens faz de 304 a 1.104 consultas (API-CUS-008, 009).
  (executado em 2026-11-22) Carregar junto as chaves estrangeiras diretas (`select_related`) levou
  `sessao/sessaoplenaria` de 304 para 4 consultas, `materia/tramitacao` de 304 para 104,
  `materia/autoria` de 404 para 204, `sessao/ordemdia` de 604 para 404 e
  `sessao/registrovotacao` de 1.104 para 804; o resto vem de `__str__` que desce dois níveis.
  Carregar as relações múltiplas de forma automática piorou `materia/materialegislativa`, de 0,6 s
  para 5 s. Caminhos avaliados: o gerador carregar as chaves diretas de todo model, mais ajuste à
  mão nas rotas pesadas; ou tirar o `__str__` da resposta padrão, que exige ajustar cerca de 140
  pontos do v6, do v2018 e dos templates.
- P2. **`expand` não prepara as consultas.** Cada relação expandida e o `__str__` de cada objeto
  expandido custam consultas por item (API-CUS-013). O número de caminhos por requisição tem teto
  (API-SER-037), mas a consulta da lista não carrega junto as relações pedidas.

## Fora do escopo

- Otimização dos serializers próprios do `painelset` e do `arq`. A das listas da LOA foi feita no
  app `loa` (LOA-PCC-080).
- Custo das actions que convertem PDF: [arquivos.md](./arquivos.md).
- Carga real de produção, índices do banco e configuração de cache.
