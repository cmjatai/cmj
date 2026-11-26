# API: serialização, `expand`, `include` e `exclude`

Status: observado, com API-SER-025 a 029, 032 a 034, 036 e 037 implementadas (acordadas em
2026-11-21 e 22, com teste) e API-SER-030 e 035 acordadas
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `drfautoapi/drfautoapi.py` (`DrfAutoApiSerializerMixin`),
`cmj/api/serializers.py` (`CmjSerializerMixin`), `sapl/api/serializers.py`,
`cmj/api/loa/serializers/__init__.py`, `sapl/api/views_parlamentares.py`
Testes: `sapl/api/tests/test_api_serializacao.py`

O que as rotas geradas devolvem por padrão, como os parâmetros `expand`, `include` e `exclude`
mudam a resposta, e quais campos internos ou pessoais chegam a anônimo.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste. As marcadas com "(executado)" foram conferidas em 2026-11-21 no banco de
desenvolvimento, como anônimo, com `django.test.Client` nas rotas reais, só com `GET` e a sessão do
banco em somente leitura. Nessas verificações foram impressos apenas nomes de campos e contagens,
nunca valores. As demais vieram da leitura do código.

## Escopo

O mixin global de serializer, os três parâmetros de consulta que mudam os campos da resposta, os
serializers próprios que escondem campos e o inventário de campos sensíveis nas rotas públicas.
Quais rotas são públicas está em [acesso.md](./acesso.md) (`API-ACS`); os filtros sobre esses
campos, em [filtros.md](./filtros.md) (`API-FIL`); o custo do `expand`, em
[paginacao-custo.md](./paginacao-custo.md) (`API-CUS`).

## Regras

### Campos por padrão

- API-SER-001 [observado] O serializer gerado herda de `CmjSerializerMixin` e devolve todos os
  campos do model (`fields = "__all__"`). (executado) 200 das 215 rotas usam o mixin global sem
  serializer próprio. Evidência: `cmj/api/serializers.py:30-56`,
  `drfautoapi/drfautoapi.py:513-514`.
- API-SER-002 [observado] Todo item ganha três campos calculados: `__str__` (`str(obj)`),
  `__label__` (nome da tabela no banco) e `link_detail_backend` (URL da tela de detalhe do model,
  ou vazio se não houver). Evidência: `drfautoapi/drfautoapi.py:686-698`,
  `cmj/api/serializers.py:53`, `cmj/api/serializers.py:174-181`.
- API-SER-003 [observado] Chave estrangeira sai como id e relação muitos-para-muitos como lista de
  ids, salvo `expand`. Evidência: `drfautoapi/drfautoapi.py:832-868`.
- API-SER-004 [observado] O mesmo serializer serve à escrita: todo campo do model é gravável por
  quem passa na permissão, salvo `owner` e `modifier` (API-SER-033). (executado) Entre os
  serializers gerados, `metadata` é gravável em 55 (com a ressalva de API-SER-034), `user` em 15
  (8 deles só para superusuário, API-SER-028), `ip` em 8 (só para superusuário) e `search` em 6;
  nos models com busca, `search` é recalculado ao salvar. Evidência:
  `drfautoapi/drfautoapi.py:501-518`.

### `expand`, `include` e `exclude`

- API-SER-005 [observado] Os três parâmetros usam a mesma sintaxe: `;` separa caminhos, `.` desce um
  nível de relação e `,` separa campos irmãos no último nível. Sem nenhum dos três, os campos não
  mudam. Evidência: `drfautoapi/drfautoapi.py:704-746`.
- API-SER-006 [observado] `expand` troca o id de uma relação pelo objeto serializado. O serializer
  usado é o que o viewset registrado para o model relacionado escolhe (`get_serializer_class`), em
  modo somente leitura. Evidência: `drfautoapi/drfautoapi.py:832-868`.
- API-SER-007 [retirada] Substituída por API-SER-025.
- API-SER-008 [observado] Expandem chave estrangeira, um-para-um e muitos-para-muitos que estejam
  entre os campos do serializer. Não expandem: relação com o model de usuário, campo calculado
  (`SerializerMethodField`) e relação reversa. Evidência: `drfautoapi/drfautoapi.py:796-827`.
- API-SER-009 [observado] Cada caminho de `expand` é cortado em 5 níveis. O número de caminhos tem
  teto (API-SER-037). Evidência: `drfautoapi/drfautoapi.py:691`,
  `drfautoapi/drfautoapi.py:770-775`.
- API-SER-037 [implementado] Uma requisição pede até 8 caminhos de `expand`. Cada trecho separado
  por ponto e vírgula é um caminho, e cada alternativa separada por vírgula num nível conta mais
  um. Acima do teto, a lista e o detalhe respondem 400 com a mensagem em `expand`. (executado) O
  maior `expand` dos frontends pede 5 caminhos. Evidência: `drfautoapi/drfautoapi.py:692`,
  `drfautoapi/drfautoapi.py:713-738`.
- API-SER-010 [observado] `expand=all` expande todas as relações do nível, só para superusuário.
  Evidência: `drfautoapi/drfautoapi.py:753-758`, `drfautoapi/drfautoapi.py:816-819`.
- API-SER-011 [observado] `include` mantém no nível indicado só os campos listados, e `exclude`
  retira os listados; os dois podem ser combinados, e `exclude` é aplicado depois. Nenhum dos dois
  acrescenta campo que o serializer não tenha. Em subnível, só valem se o campo pai estiver
  expandido. Evidência: `drfautoapi/drfautoapi.py:778-794`.
- API-SER-012 [observado] Erro ao expandir um campo é registrado em log, e o campo segue como id.
  Evidência: `drfautoapi/drfautoapi.py:865-868`.
- API-SER-013 [observado] A expansão não acrescenta `select_related` nem `prefetch_related`.
  Evidência: `drfautoapi/drfautoapi.py:683`.

### Serializers que escondem campos

- API-SER-014 [retirada] Substituída por API-SER-027.
- API-SER-015 [retirada] Substituída por API-SER-027.
- API-SER-016 [observado] `loa/emendaloa` retira `owner`, `metadata` e `search` dentro do próprio
  serializer: do serializer inteiro para quem não os vê em emenda nenhuma (API-FIL-022), e objeto
  a objeto para quem não pode editar aquela emenda. Por estar na classe, a regra vale também quando
  a emenda chega por `expand`. O `owner` segue ainda API-SER-032: quem edita a emenda sem ter
  `list_emendaloa`, como o operador do autor, recebe `metadata` e `search`, mas não `owner`.
  Evidência: `cmj/api/loa/serializers/__init__.py:101-124`.
- API-SER-017 [retirada] Substituída por API-SER-025.
- API-SER-018 [retirada] Substituída por API-SER-026.
- API-SER-025 [implementado] `expand` só troca o id pelo objeto se o usuário passar nas permissões
  de leitura do viewset do model relacionado, conferidas como numa listagem e como `GET`, qualquer
  que seja o método da requisição. Se não passar, ou se a conferência falhar, o campo segue como
  id. Evidência: `drfautoapi/drfautoapi.py:839-843`, `drfautoapi/drfautoapi.py:872-922`.
- API-SER-026 [implementado] Um objeto que o usuário não veria na rota do model relacionado, por
  estar fora do `get_queryset` do viewset dele, sai como id mesmo com `expand`, inclusive dentro de
  uma lista. A conferência só acontece quando o viewset tem `get_queryset` próprio ou queryset
  filtrado, custa uma consulta por objeto distinto na requisição, e erro conta como não visível.
  Evidência: `drfautoapi/drfautoapi.py:319-325`, `drfautoapi/drfautoapi.py:920-921`, `drfautoapi/drfautoapi.py:928-961`.
- API-SER-027 [implementado] O serializer de parlamentar segue o que a tela pública mostra. Retira
  13 campos pessoais para quem não tem `parlamentares.add_parlamentar`: `cpf`, `rg`,
  `titulo_eleitor`, `endereco_residencia`, `municipio_residencia`, `uf_residencia`,
  `cep_residencia`, `telefone_residencia`, `fax`, `fax_residencia`, `situacao_militar`,
  `data_nascimento` e `sexo`. O `email` e o `telefone`, contato do mandato que a página do
  parlamentar exibe, saem para todos. A regra fica na classe do serializer e vale na rota do
  parlamentar, no `expand` de qualquer rota e em todo outro uso do serializer; sem requisição no
  contexto, os campos também não saem. Evidência: `sapl/api/serializers.py:89-119`,
  `_templates/v2018/parlamentares/layouts.yaml:46-62`.
- API-SER-028 [implementado] Num model que guarda quem fez o registro, pelo par de campos `ip` e
  `user`, os dois só saem para superusuário, como nas telas de detalhe desses models. Hoje são
  oito: matéria legislativa, proposição, tramitação, norma jurídica, tramitação administrativa,
  registro de votação, voto de parlamentar e registro de leitura. A regra fica no serializer
  padrão e vale na rota, no `expand`, nas actions que devolvem o model, no canal de sincronização
  por WebSocket e na escrita: quem não recebe os campos também não os grava. Sem requisição no
  contexto, os campos não saem. O campo `user` de um model que não tem `ip` não é afetado.
  Evidência: `cmj/api/serializers.py:64-69`, `cmj/api/serializers.py:110-119`,
  `_templates/v2018/materia/materialegislativa_detail.html:230-261`.
- API-SER-029 [implementado] Dentro de `metadata`, as chaves que descrevem o armazenamento dos
  arquivos do registro (`s3_aws`, `s3_cmj` e `locaweb`: caminho, hash e tamanho) só saem para
  superusuário. As demais chaves saem como estão. A regra fica no serializer padrão e vale na
  rota, no `expand` e no canal de sincronização por WebSocket; sem requisição no contexto, essas
  chaves não saem. O `metadata` gravado no registro não muda. Evidência:
  `cmj/api/serializers.py:51`, `cmj/api/serializers.py:74-98`.
- API-SER-032 [implementado] Uma relação com o model de usuário, fora do par de API-SER-028, só sai
  para quem tem a permissão de listagem do próprio model (`list_<model>`). Quem lê a rota pelo
  mapa público, sem essa permissão, não recebe o campo: hoje `operadores` em `base/autor`, `owner`
  em `compilacao/nota` e `owners` em `compilacao/textoarticulado`. Nas rotas restritas nada muda,
  porque quem as lê tem a permissão. A regra fica no serializer padrão e vale na rota, no `expand`
  e no canal de sincronização; sem requisição no contexto, o campo não sai. Evidência:
  `cmj/api/serializers.py:64-72`, `cmj/api/serializers.py:100-132`.
- API-SER-033 [implementado] Nas gravações pela API, `owner` e `modifier` são preenchidos pelo
  servidor com o usuário da requisição: `owner` na criação e `modifier` em toda gravação. Os dois
  são somente leitura para o cliente, e o valor enviado neles é ignorado, para qualquer usuário.
  Evidência: `cmj/api/serializers.py:58-62`, `cmj/api/serializers.py:82-90`,
  `cmj/api/serializers.py:134-145`.
- API-SER-034 [implementado] Na gravação de `metadata` por quem não é superusuário, as chaves de
  armazenamento (API-SER-029) ficam como estão no registro: o cliente não as cria, não as altera
  e, ao devolver um `metadata` sem elas, não as apaga. As demais chaves são gravadas como
  enviadas. Evidência: `cmj/api/serializers.py:154-172`.
- API-SER-036 [implementado] `protocoloadm/documentoadministrativo` segue o que a tela mostra. Saem
  para todos os que alcançam o documento, inclusive anônimo na área de trabalho pública, os campos
  que a tela pública exibe, entre eles `interessado`, `email` e `observacao`. O código de
  compartilhamento (`link_share`) e os campos de importação do sistema antigo (`old_path`,
  `old_json` e `temp_migracao_sislegis`), que tela nenhuma mostra, só saem para quem tem
  `list_documentoadministrativo`. (executado) Na área pública da base local, 2 documentos têm
  `interessado`, nenhum tem `email` ou `link_share`, e 1.610 têm os campos de importação.
  Evidência: `sapl/api/serializers.py:66-86`,
  `_templates/v2018/protocoloadm/documentoadministrativo_item_filter.html:88-91`.

### Campos internos e pessoais nas rotas públicas

- API-SER-019 [retirada] Substituída por API-SER-028.
- API-SER-020 [retirada] Substituída por API-ACS-032.
- API-SER-021 [retirada] Substituída por API-SER-027.
- API-SER-022 [retirada] Substituída por API-SER-036.
- API-SER-023 [retirada] Substituída por API-SER-029, API-SER-030 e API-SER-031.
- API-SER-030 [acordado] As assinaturas digitais extraídas dos arquivos (`metadata.signs`: nome do
  signatário, como consta do certificado, e data) são dado público na API, como nas telas, que
  mostram os mesmos nomes e datas. O nome pode trazer o número de documento que o certificado
  carrega: ele está no próprio PDF assinado, servido ao público. Evidência:
  `_templates/v2018/core/sign_widget.html:3-27`, `cmj/core/signals_functions.py:279-318`.
- API-SER-031 [observado] (executado) 34 rotas públicas devolvem `metadata`. Além das assinaturas
  (11 rotas), saem: `scrap`, com os dados raspados do portal de transparência, em 8 rotas da LOA
  (a aba de empenhos do painel do v2018 lê `scrap.values`); `selos`; `zipfile`, com os nomes dos
  arquivos do zip do documento administrativo; `send`, com a data de envio a rede social; e
  `import_fields`, em `loa/entidade`. `scrap.values` traz `CpfCnpjCredor` e `import_fields` traz
  `NU_CPF`: é a mesma decisão de transparência do painel de prestação de contas da LOA, que os
  aceitou como dado público (LOA-PCL-087 e 088). Os filtros gerados sobre `metadata` não devolvem
  resultado para valor nenhum, salvo `isnull`. Evidência: `drfautoapi/drfautoapi.py:513-514`,
  `_frontend/v2018/src/modules/loa/pcl/tabs/PclTabEmpenhos.vue:202-208`.
- API-SER-024 [observado] (executado) Outros campos internos em rotas públicas: `hash_code` em
  `materia/proposicao`, `cpfcnpj` em `loa/entidade` e `loa/empenho`, e `search` em `loa/empenho` e
  `loa/registroajusteloa`, que é o texto normalizado de campos que a rota já entrega. Evidência:
  `drfautoapi/drfautoapi.py:513-514`.
- API-SER-035 [acordado] `__label__` faz parte da resposta: os três frontends o usam para saber de
  que model é cada item, e ele repete o que a URL da rota já diz (`<app>_<model>`). Evidência:
  `drfautoapi/drfautoapi.py:697-698`, `_frontend/v6/src/modules/sessao/ItemDeSessao.vue:3-4`.

## Riscos de segurança

Varredura de 2026-11-21, item 2 de `docs/specs/README.md` (dados pela API), sobre o mixin global e
as rotas públicas, revista em 2026-11-22. Os valores dos campos não foram lidos nem copiados.

Nenhum risco encontrado no item 2 (2026-11-22).

## Dúvidas

Nenhuma dúvida em aberto.

## Fora do escopo

- Os serializers próprios da LOA, do `painelset`, do `arq` e de `DocumentoViewSet`, além do que
  escondem ou expõem na lista acima.
- O documento do fornecedor (`cpfcnpj` em `loa/empenho` e `loa/entidade`, e os campos equivalentes
  dentro de `metadata`, API-SER-031): é decisão de transparência do painel de prestação de contas
  da LOA, que o aceitou como dado público (LOA-PCL-087 e 088). A forma de esconder um campo está
  definida aqui: regra na classe do serializer (API-SER-027, 028, 029 e 032).
- Filtros e ordenação sobre campos ocultos: [filtros.md](./filtros.md).
- Renderers e arquivos: [arquivos.md](./arquivos.md).
