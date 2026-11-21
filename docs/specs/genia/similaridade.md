# Genia: análise de similaridade entre matérias

Status: observado, exceto as regras marcadas como acordado ou implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/similaridade.py`, `cmj/utils/genia/prompts_similaridade.py`,
`sapl/base/tasks.py`
Testes: `cmj/utils/genia/test_genia.py` (o fluxo de batch não tem teste)

As regras `[observado]` vêm da leitura do código, sem executar o fluxo nem chamar a API. As
`[acordado]` foram decididas e implementadas em 2026-11-19, ainda sem teste.

## Escopo

`IAAnaliseSimilaridadeService`: compara os textos originais de duas matérias e grava parecer e
percentual em `AnaliseSimilaridade`, de forma síncrona ou em batch.

## Regras

### Prompt e resposta

- GENIA-SIM-002 [implementado] O prompt em uso é `PROMPT_V2`, preenchido com os dois textos e as
  epígrafes curtas das matérias. Os outros prompts do módulo são histórico. Evidência:
  `cmj/utils/genia/similaridade.py:31-41`, `cmj/utils/genia/prompts_similaridade.py:87`.
- GENIA-SIM-004 [observado] Os textos vêm do PDF do texto original de cada matéria, com a mesma
  extração da classificação (GENIA-CLA-004). Evidência: `cmj/utils/genia/similaridade.py:52-60`.
- GENIA-SIM-001 [implementado] O percentual é o número entre `[[` e `%` da resposta. Resposta sem
  essa marcação grava similaridade 0. A análise recebe também o texto integral, o modelo usado e a
  data. Evidência: `cmj/utils/genia/similaridade.py:62-74`.

### Execução síncrona

- GENIA-SIM-003 [implementado] `run` consome a cota autorizada para a chave
  `IAAnaliseSimilaridadeService`, escolhendo a de maior `quota_diaria`, responde em `text/plain` e
  salva a análise, a menos que receba `save=False`. Com `quota=`, repassa a cota já obtida
  (GENIA-BASE-015). Evidência: `cmj/utils/genia/similaridade.py:28-29`,
  `cmj/utils/genia/similaridade.py:76-89`.

### Execução em batch

- GENIA-SIM-005 [observado] `batch_run` cria `get_threads` jobs na API de batch, com até
  `batch_size` análises cada. Os dois valores vêm da `IAQuota` selecionada. As análises além desse
  total ficam para outra execução. Evidência: `cmj/utils/genia/similaridade.py:91-140`.
- GENIA-SIM-006 [acordado] As requisições do batch usam a mesma configuração de geração da
  execução síncrona (temperatura, `top_k`, `top_p`, mime type), vinda de `build_generation_config`.
  Evidência: `cmj/utils/genia/similaridade.py:102-104`, `cmj/utils/genia/similaridade.py:124`.
- GENIA-SIM-007 [observado] O método bloqueia, consultando os jobs a cada 60 segundos, até todos
  chegarem a um estado final. Job que não termina com sucesso só gera log de erro. Evidência:
  `cmj/utils/genia/similaridade.py:144-182`.
- GENIA-SIM-008 [acordado] Cada resposta com texto registra um consumo de peso 1 e salva a
  análise, casada com a requisição pela posição original (resposta vazia não desloca as seguintes).
  A margem da cota só é verificada uma vez, antes de criar os jobs. Evidência:
  `cmj/utils/genia/similaridade.py:97`, `cmj/utils/genia/similaridade.py:150-163`.

### Quem chama

- GENIA-SIM-009 [acordado] Com uma matéria específica, a task obtém a cota uma vez e analisa até
  100 pares de forma síncrona; falha em um par é registrada e o laço segue. Sem matéria, usa o batch.
  As duas tasks Celery não executam com `DEBUG=True`. Evidência: `sapl/base/tasks.py:255-266`.

## Decisões

- A margem da cota é verificada uma vez, antes de criar os jobs. A última execução do batch pode
  registrar até `batch_size × get_threads` consumos, acima do que restava (GENIA-SIM-008). Aceito.

## Mudança de comportamento na refatoração

O modo síncrono exigia a marcação com espaço (`[[ 85% ]]`). Agora aceita também `[[85%]]`, como o
batch já aceitava.

## Fora do escopo

Criação dos registros de `AnaliseSimilaridade` e a seleção dos pares em `sapl/base/tasks.py`.
