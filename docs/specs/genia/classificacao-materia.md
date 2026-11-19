# Genia: classificação de matéria

Status: observado, exceto a cota (GENIA-CLA-001, implementado)
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/classificacao.py`, `cmj/utils/genia/extracao.py`,
`sapl/materia/views.py`, `sapl/base/tasks.py`
Testes: `cmj/utils/genia/test_genia.py` (só a chave de cota)

As regras `[observado]` vêm da leitura do código, sem executar o fluxo nem chamar a API.

## Escopo

`IAClassificacaoMateriaService`: gera e remove a análise por I.A. de uma matéria legislativa, gravada
em `Metadata` na chave `genia`.

## Regras

### Cota e modelo

- GENIA-CLA-001 [implementado] O serviço consome a cota autorizada para a chave
  `IAClassificacaoMateriaService`, escolhendo a de maior `quota_diaria` com margem. Evidência:
  `cmj/utils/genia/classificacao.py:27`, `cmj/utils/genia/classificacao.py:192`.
- GENIA-CLA-002 [observado] O `ia_model_name` do prompt YAML não define o modelo usado: a seleção da
  cota o substitui antes da chamada. O `model_name` gravado na análise é o da cota. Evidência:
  `cmj/utils/genia/classificacao.py:152`, `cmj/utils/genia/base.py:76`.

### Entrada

- GENIA-CLA-003 [observado] `model` e `object` precisam ser definidos antes de `run`. `object` aceita
  instância ou id, e levanta "Registro não encontrado." para id inexistente. Evidência:
  `cmj/utils/genia/classificacao.py:36-76`.
- GENIA-CLA-004 [observado] O contexto é o texto limpo de todos os PDFs listados em
  `FIELDFILE_NAME` do objeto, concatenados. Página com mais de 10% de caracteres de uso privado passa
  por OCR. Evidência: `cmj/utils/genia/classificacao.py:173-182`,
  `cmj/utils/genia/extracao.py:17-44`.
- GENIA-CLA-005 [observado] O prompt vem do campo `prompt` do tipo da matéria, em YAML, com a lista
  `PROMPTs`. Vale o primeiro item com `status` verdadeiro, e a `mask` dele recebe o texto em
  `{context}`. Sem prompt, sem item ativo ou sem `mask`, nada é gerado. Evidência:
  `cmj/utils/genia/classificacao.py:133-171`, `sapl/materia/models.py:220`.
- GENIA-CLA-006 [observado] Na ação `generate`, temperatura, `top_k` e `top_p` vêm do item do YAML.
  Na `generate_custom`, vêm da query string. Evidência: `cmj/utils/genia/classificacao.py:151-160`.

### Ações

- GENIA-CLA-007 [observado] Com `request`, a ação vem de `?ia_run=`. Sem `request`, vem do argumento
  `action`. O padrão é `generate`. Evidência: `cmj/utils/genia/classificacao.py:78-93`.
- GENIA-CLA-008 [observado] Toda ação `generate*` apaga antes todos os `Metadata` do objeto, não só a
  chave `genia`. Se a geração falhar depois, a análise anterior já foi perdida. Evidência:
  `cmj/utils/genia/classificacao.py:95-100`, `cmj/utils/genia/classificacao.py:108-112`.
- GENIA-CLA-009 [observado] A resposta precisa ser JSON. Ela é gravada em `Metadata.metadata["genia"]`
  com `model_name`, `template` (`table1`), `temperature`, `top_k` e `top_p`. Evidência:
  `cmj/utils/genia/classificacao.py:194-206`.
- GENIA-CLA-010 [observado] Qualquer erro na geração é registrado em log e não sobe: `generate`
  devolve `None`. Com `request`, o usuário vê "Ocorreu erro na geração da análise!". Evidência:
  `cmj/utils/genia/classificacao.py:221-229`.
- GENIA-CLA-011 [observado] A ação `delete` remove os `Metadata` do objeto e, com `request`, avisa
  "Análise removida com sucesso!". Evidência: `cmj/utils/genia/classificacao.py:101-106`.

### Quem chama

- GENIA-CLA-012 [observado] Na tela da matéria, `?ia_run=` só executa para quem tem
  `core.generate_analise_genia`. Os `temas` da análise viram `AssuntoMateria` e `MateriaAssunto`, e em
  seguida a análise de similaridade da matéria é disparada. Evidência:
  `sapl/materia/views.py:2940-2991`.
- GENIA-CLA-013 [observado] A task `task_classifica_materialegislativa` classifica uma matéria por
  execução, de 2024 ou anterior, e está desativada. Evidência: `sapl/base/tasks.py:56-125`.

## Dúvidas

- D1. A geração apaga todos os `Metadata` do objeto antes de chamar a I.A. (GENIA-CLA-008). Uma falha
  de cota ou de API deixa a matéria sem análise. A remoção deve acontecer só depois de a nova análise
  estar pronta, e só da chave `genia`?
- D2. O `ia_model_name` do YAML é ignorado (GENIA-CLA-002). Ele deveria restringir a cota a esse
  modelo, ou o campo pode sair do YAML?
- D3. Sem cota, o erro é engolido (GENIA-CLA-010) e o usuário vê a mensagem genérica. Deve informar
  que a cota acabou?
- D4. Na ação `generate` com `request`, `temperature`, `top_k` e `top_p` lidos da query string ficam
  como texto (`cmj/utils/genia/classificacao.py:97-99`) até o YAML sobrescrevê-los. Se o YAML não
  trouxer o parâmetro, o texto segue para a API. A conversão deve ser feita na leitura?
- D5. `yaml.load` usa `FullLoader` em texto editável no cadastro de tipos de matéria
  (`cmj/utils/genia/classificacao.py:140`). Trocar por `safe_load`?

## Fora do escopo

Templates que exibem a análise (`_templates/v2018/materia/materialegislativa_genia_table1.html`) e a
substituição de temas em `sapl/materia/forms.py`.
