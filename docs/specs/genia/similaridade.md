# Genia: análise de similaridade entre matérias

Status: observado, exceto as regras marcadas como implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/similaridade.py`, `cmj/utils/genia/prompts_similaridade.py`,
`sapl/base/tasks.py`
Testes: `cmj/utils/genia/test_genia.py` (o fluxo de batch não tem teste)

As regras `[observado]` vêm da leitura do código, sem executar o fluxo nem chamar a API.

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
  salva a análise, a menos que receba `save=False`. Evidência:
  `cmj/utils/genia/similaridade.py:28-29`, `cmj/utils/genia/similaridade.py:76-87`.

### Execução em batch

- GENIA-SIM-005 [observado] `batch_run` cria `get_threads` jobs na API de batch, com até `batch_size`
  análises cada. Os dois valores vêm da `IAQuota` selecionada. As análises além desse total ficam
  para outra execução. Evidência: `cmj/utils/genia/similaridade.py:95-137`.
- GENIA-SIM-006 [observado] As requisições do batch enviam só `response_mime_type`: temperatura,
  `top_k` e `top_p` ficam no padrão da API, diferente da execução síncrona. Evidência:
  `cmj/utils/genia/similaridade.py:117-119`.
- GENIA-SIM-007 [observado] O método bloqueia, consultando os jobs a cada 60 segundos, até todos
  chegarem a um estado final. Job que não termina com sucesso só gera log de erro. Evidência:
  `cmj/utils/genia/similaridade.py:139-180`.
- GENIA-SIM-008 [observado] Cada resposta com texto registra um consumo de peso 1 e salva a análise.
  A margem da cota só é verificada uma vez, antes de criar os jobs. Evidência:
  `cmj/utils/genia/similaridade.py:95`, `cmj/utils/genia/similaridade.py:152-160`.

### Quem chama

- GENIA-SIM-009 [observado] Com uma matéria específica, a task analisa até 100 pares de forma
  síncrona. Sem matéria, usa o batch. As duas tasks Celery não executam com `DEBUG=True`. Evidência:
  `sapl/base/tasks.py:255-282`.

## Dúvidas

- D1. No batch, as respostas sem conteúdo são descartadas antes de casar resposta com análise pela
  posição (`cmj/utils/genia/similaridade.py:147-158`). Se uma requisição do meio falhar, as análises
  seguintes recebem o parecer de outro par. O casamento deve usar a posição original?
- D2. O batch verifica a margem uma vez e pode registrar `batch_size × get_threads` consumos, acima
  do que restava da cota (GENIA-SIM-008). Limitar a quantidade enviada à margem restante?
- D3. No modo síncrono, a primeira falha de cota interrompe o laço de até 100 pares, e a exceção é
  registrada pela task. É o comportamento pretendido?
- D4. Batch e síncrono usam parâmetros de geração diferentes (GENIA-SIM-006). Devem ser iguais?

## Mudança de comportamento na refatoração

O modo síncrono exigia a marcação com espaço (`[[ 85% ]]`). Agora aceita também `[[85%]]`, como o
batch já aceitava.

## Fora do escopo

Criação dos registros de `AnaliseSimilaridade` e a seleção dos pares em `sapl/base/tasks.py`.
