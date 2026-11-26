# API: filtros e ordenação gerados

Status: observado, com API-FIL-020, 021, 022 e 026 a 028 implementadas (acordadas em 2026-11-21 e
22, com teste) e API-FIL-024 e 025 acordadas (2026-11-22)
Última verificação: 2026-11-21 (commit `2452ae3d8`)
Código principal: `drfautoapi/drfautoapi.py` (`ApiFilterSetMixin`, `SplitStringCharFilter`,
`M2MFilter`), `cmj/api/forms.py`, `sapl/api/forms.py`
Testes: `sapl/api/tests/test_api_filtros.py`, `cmj/loa/tests/test_listagem_emendas.py`

Os parâmetros de consulta que filtram e ordenam as listas das rotas geradas: quais nascem
automaticamente de cada model, como tratam o valor recebido e o que alcançam além dos campos que a
resposta mostra.

As regras `[observado]` descrevem o que o código faz hoje e não foram confirmadas como regra
desejada; as `[implementado]` foram acordadas e têm teste. As marcadas com "(executado)" foram conferidas em 2026-11-21 no banco de
desenvolvimento, como anônimo, com `django.test.Client` nas rotas reais, só com `GET` e a sessão do
banco em somente leitura; quando o filtro toca campo oculto, só contagens foram impressas. As
demais vieram da leitura do código.

## Escopo

O filterset global (`CmjFilterSetMixin`, que herda `ApiFilterSetMixin` sem acrescentar nada), a
geração de filtros por campo, os parâmetros `o` e `id__in` e o tratamento de erro. Os filtersets
próprios (`AutorFilterSet`, `SessaoPlenariaFilterSet`, os três da LOA) entram só pelo que herdam.
Como o filterset é escolhido está em [gerador.md](./gerador.md) (`API-GER`).

## Regras

### Geração

- API-FIL-001 [observado] O filterset é gerado com filtros para todos os campos do model
  (`fields = "__all__"`). Quais deles valem numa requisição depende do usuário (API-FIL-020).
  Evidência: `drfautoapi/drfautoapi.py:90-91`, `cmj/api/forms.py:17-18`.
- API-FIL-002 [observado] Para cada campo é criado um filtro por lookup registrado no Django para o
  tipo do campo, inclusive os encadeados em transformações (`data__year__gte`), mais `range`. Ficam
  de fora `contained_by`, `trigram_similar`, `unaccent`, `search` e os de expressão regular
  (API-FIL-027). Evidência: `drfautoapi/drfautoapi.py:182-227`.
- API-FIL-003 [observado] (executado) Um campo de texto recebe 17 filtros (entre eles `icontains`,
  `startswith`, `gt`, `lt`, `range` e dois de trigrama); um campo de data, 63; um JSON, 18 (com
  `has_key` e `icontains`); uma chave estrangeira, 7 (`exact`, `in`, `isnull` e comparações).
  Evidência: `drfautoapi/drfautoapi.py:193-227`.
- API-FIL-004 [observado] Relação muitos-para-muitos recebe só `exact` e `in`; o `in` aceita ids
  separados por vírgula. Evidência: `drfautoapi/drfautoapi.py:187-189`,
  `drfautoapi/drfautoapi.py:70-82`, `drfautoapi/drfautoapi.py:254-260`.
- API-FIL-005 [observado] Os filtros não atravessam relações: para uma chave estrangeira existe
  `user=<id>`, e não `user__email=`. Atravessar exige declarar o filtro num filterset próprio.
  Evidência: `drfautoapi/drfautoapi.py:182-227`.
- API-FIL-006 [observado] (executado) O número de filtros por rota vai de 16 a 904, com mediana de
  112 e 40.407 no total das 215 rotas. Os maiores: `compilacao/dispositivo` (904), `sigad/classe`
  (888) e `protocoloadm/protocolo` (874). Evidência: `drfautoapi/drfautoapi.py:170-234`.
- API-FIL-007 [retirada] Substituída por API-FIL-026.
- API-FIL-026 [implementado] A cada requisição o filterset instancia só os filtros gerados que ela
  cita, mais os declarados à mão; a classe continua com todos, e é dela que o esquema OpenAPI os
  lê. (executado) Montar o filterset leva cerca de 1 ms com dois filtros citados e 0,2 ms sem
  nenhum, em `materia/materialegislativa`, `materia/tramitacao` e `compilacao/dispositivo`;
  instanciar todos levava de 25 a 60 ms. A conferência dos campos legíveis (API-FIL-020, 021)
  acrescenta de 1 a 2 ms por requisição com filtro gerado e cerca de 6 ms na ordenação por
  relação. Evidência: `drfautoapi/drfautoapi.py:113-131`, `drfautoapi/drfautoapi.py:971-998`.
- API-FIL-027 [implementado] Não há filtro gerado por expressão regular: `regex` e `iregex` ficam
  fora da geração, e o parâmetro com um desses sufixos é ignorado como qualquer parâmetro
  desconhecido (API-FIL-028). Evidência: `drfautoapi/drfautoapi.py:193-208`.

### Tratamento dos valores

- API-FIL-008 [observado] Em campo de texto, `icontains` quebra o valor nos espaços e exige todos
  os termos; um trecho entre aspas duplas é buscado inteiro. (executado) Em
  `materia/materialegislativa`, `ementa__icontains=lei municipal` devolve 791 itens e com aspas,
  232. Evidência: `drfautoapi/drfautoapi.py:36-67`, `drfautoapi/drfautoapi.py:99-104`.
- API-FIL-009 [observado] Campo de arquivo e campo JSON são filtrados como texto, por igualdade.
  Evidência: `drfautoapi/drfautoapi.py:93-98`, `drfautoapi/drfautoapi.py:105-110`.
- API-FIL-010 [observado] (executado) Valor inválido para o tipo do filtro responde 400 com a
  mensagem do campo; id inexistente numa chave estrangeira também responde 400 ("escolha
  inválida"), em todas as rotas (API-GER-037). Evidência: `drfautoapi/drfautoapi.py:236-252`.
- API-FIL-011 [observado] (executado) Parâmetro que não corresponde a nenhum filtro é ignorado, e a
  lista vem sem filtro. Evidência: `drfautoapi/drfautoapi.py:300-301`.
- API-FIL-012 [retirada] Substituída por API-FIL-027.
- API-FIL-028 [implementado] Parâmetro que não corresponde a nenhum filtro, expressão inválida em
  `o` e valor inválido em `id__in` são ignorados em silêncio, e a lista vem como viria sem eles
  (API-FIL-011, 015, 016). Mantido por decisão de 2026-11-22: as regras de API-FIL-020 e 021
  dependem de ignorar filtro e ordenação de campo que o usuário não recebe, e responder erro a
  parâmetro desconhecido exigiria conhecer, rota por rota, os parâmetros que não são filtro.
  Evidência: `drfautoapi/drfautoapi.py:118-131`, `drfautoapi/drfautoapi.py:156-168`.

### `o` e `id__in`

- API-FIL-013 [observado] `o` ordena a lista por uma ou mais expressões separadas por vírgula,
  passadas a `order_by` depois da conferência de API-FIL-021. Evidência:
  `drfautoapi/drfautoapi.py:87`, `drfautoapi/drfautoapi.py:163-168`.
- API-FIL-014 [retirada] Substituída por API-FIL-021.
- API-FIL-015 [observado] (executado) Expressão inválida em `o` é ignorada, e a lista vem na ordem
  padrão do model. Evidência: `drfautoapi/drfautoapi.py:164-168`.
- API-FIL-016 [observado] `id__in` filtra por uma lista de ids separados por vírgula; (executado)
  valor inválido é ignorado e a lista vem inteira. Evidência: `drfautoapi/drfautoapi.py:88`,
  `drfautoapi/drfautoapi.py:156-161`.

### Campos que o usuário recebe

- API-FIL-017 [retirada] Substituída por API-FIL-020.
- API-FIL-018 [retirada] Substituída por API-FIL-022.
- API-FIL-019 [retirada] Substituída por API-SER-028.
- API-FIL-020 [implementado] Um filtro gerado só vale para campo que o serializer da rota entrega
  ao usuário da requisição, sem contar `expand`, `include` e `exclude`. O filtro de campo que o
  usuário não recebe sai do filterset, e o parâmetro é ignorado como qualquer parâmetro
  desconhecido (API-FIL-011). Filtros declarados à mão num filterset próprio não passam por essa
  conferência. Se o serializer não puder ser montado, nenhum filtro gerado vale. Evidência:
  `drfautoapi/drfautoapi.py:113-154`, `drfautoapi/drfautoapi.py:971-998`,
  `drfautoapi/drfautoapi.py:706`.
- API-FIL-021 [implementado] `o` só ordena por campo que o usuário recebe. Um caminho com relação
  (`materia__tipo__sigla`) só vale se cada passo for um campo legível e se o usuário puder ler a
  rota do model relacionado, pela mesma conferência do `expand` (API-SER-025); nunca atravessa o
  model de usuário. Basta um termo fora disso para a ordenação inteira ser ignorada. `?` (ordem
  aleatória) continua valendo. Evidência: `drfautoapi/drfautoapi.py:163-168`,
  `drfautoapi/drfautoapi.py:1001-1048`.
- API-FIL-022 [implementado] Em `loa/emendaloa`, `owner`, `metadata` e `search` saem do serializer
  inteiro para quem não os vê em emenda nenhuma: anônimo e usuário sem permissão de edição e sem
  autor. Para esses usuários os três campos não valem como filtro nem como ordenação. Quem pode
  vê-los em alguma emenda continua filtrando por eles; `owner` exige ainda `list_emendaloa`
  (API-SER-032). Evidência:
  `cmj/api/loa/serializers/__init__.py:107-116`, `cmj/loa/services/s_emendaloa.py:171-183`.
- API-FIL-024 [acordado] Em `loa/emendaloa`, quem vê `metadata` e `search` em alguma emenda filtra
  e ordena por eles em todas, inclusive nas emendas em que não os recebe: é o caso do operador de
  autor diante das emendas dos outros autores. Aceito em 2026-11-22 porque não há o que revelar:
  (executado) o `metadata` das 907 emendas da base local só guarda `style`, o layout de impressão,
  e o `search` é a epígrafe, o texto dos artigos e os parlamentares, que a busca da listagem
  pública já pesquisa para qualquer usuário. Guardar conteúdo reservado no `metadata` da emenda
  exige rever esta regra. Evidência: `cmj/loa/services/s_emendaloa.py:171-183`,
  `cmj/api/forms.py:116-131`, `cmj/loa/models/m_emendaloa.py:376-398`,
  `cmj/loa/forms/f_emendaloa.py:672`.
- API-FIL-025 [acordado] A conferência da ordenação por relação (API-FIL-021) é por rota, e não
  objeto a objeto: a ordem da lista pode refletir um atributo de um objeto relacionado que o
  `expand` não mostraria ao usuário. Aceito em 2026-11-22: revela só a posição relativa, os filtros
  não atravessam relações (API-FIL-005), e barrar a ordenação para models com visibilidade por
  registro impediria ordenações em que a própria lista já vem restrita, como a de tramitações
  administrativas pelo documento. Evidência: `drfautoapi/drfautoapi.py:1022-1048`.
- API-FIL-023 [observado] (executado) Hoje têm filtros gerados sobre campos que o serializer não
  entrega: `parlamentares/parlamentar` (os 13 campos pessoais, para quem não tem
  `parlamentares.add_parlamentar`), `materia/materialegislativa` (`similaridades`),
  `sigad/documento` (6 campos), as oito rotas de API-SER-028 (`ip` e `user`, para quem não é
  superusuário: `user=<id>`, inclusive com id inexistente, `ip=` e `o=user` são ignorados) e as
  três de API-SER-032 (`operadores`, `owner` e `owners`, para quem não lista o model) e
  `protocoloadm/documentoadministrativo` (os quatro campos de API-SER-036). Nenhum
  frontend ou template usa esses filtros, e as 15 expressões de ordenação que eles enviam
  continuam valendo. Evidência: `drfautoapi/drfautoapi.py:113-154`.

## Riscos de segurança

Varredura de 2026-11-21, itens 1, 2 e 7 de `docs/specs/README.md`, sobre os filtros gerados. O
custo das consultas que os filtros permitem está em [paginacao-custo.md](./paginacao-custo.md).

Nenhum risco encontrado nos itens 1, 2 e 7 (2026-11-22).

## Dúvidas

Nenhuma dúvida em aberto.

## Fora do escopo

- Os filtros declarados à mão nos filtersets próprios (`q`, `search`, `situacao`, `year`, `month`,
  `loa`) e as regras de negócio deles.
- O `SearchFilter` do DRF, declarado nas settings e não usado pelas rotas geradas (API-GER-010).
- Custo das consultas com filtros e ordenação: [paginacao-custo.md](./paginacao-custo.md).
