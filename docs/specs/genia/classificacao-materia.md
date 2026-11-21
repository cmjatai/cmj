# Genia: classificação de matéria

Status: observado, exceto as regras marcadas como implementado
Última verificação: 2026-11-19 (branch `master`, sobre o commit `98243939a`)
Código principal: `cmj/utils/genia/classificacao.py`, `cmj/utils/genia/extracao.py`,
`sapl/materia/views.py`, `sapl/base/tasks.py`,
`sapl/materia/migrations/0003_remove_ia_model_name_do_prompt.py`
Testes: `cmj/utils/genia/test_genia.py`

As regras `[observado]` vêm da leitura do código, sem executar o fluxo nem chamar a API.

## Escopo

`IAClassificacaoMateriaService`: gera e remove a análise por I.A. de uma matéria legislativa, gravada
em `Metadata` na chave `genia`.

## Regras

### Cota e modelo

- GENIA-CLA-001 [implementado] O serviço consome a cota autorizada para a chave
  `IAClassificacaoMateriaService`, escolhendo a de maior `quota_diaria` com margem. A cota é obtida
  antes da extração de texto. Evidência: `cmj/utils/genia/classificacao.py:27`,
  `cmj/utils/genia/classificacao.py:223-226`. Teste:
  `test_classificacao_usa_maior_cota_e_ignora_modelo_do_yaml`.
- GENIA-CLA-002 [implementado] O modelo é sempre o da cota. Um `ia_model_name` que ainda esteja no
  YAML é ignorado. O `model_name` gravado na análise é o da cota. Evidência:
  `cmj/utils/genia/classificacao.py:174-184`, `cmj/utils/genia/base.py:76`. Teste:
  `test_classificacao_usa_maior_cota_e_ignora_modelo_do_yaml`.
- GENIA-CLA-014 [implementado] A migration `materia.0003` remove as linhas `ia_model_name:` dos
  prompts gravados, sem reescrever o resto do texto. Só aplica se o YAML resultante equivaler ao
  original sem a chave. Caso contrário, mantém o prompt e registra aviso no log. Evidência:
  `sapl/materia/migrations/0003_remove_ia_model_name_do_prompt.py`. Teste:
  `test_migration_remove_ia_model_name_sem_reescrever_o_yaml`.
  Evidência: `sapl/materia/migrations/0003_remove_ia_model_name_do_prompt.py:27-60`.

### Entrada

- GENIA-CLA-003 [observado] `model` e `object` precisam ser definidos antes de `run`. `object` aceita
  instância ou id, e levanta "Registro não encontrado." para id inexistente. Evidência:
  `cmj/utils/genia/classificacao.py:36-76`.
- GENIA-CLA-004 [observado] O contexto é o texto limpo de todos os PDFs listados em
  `FIELDFILE_NAME` do objeto, concatenados. Página com mais de 10% de caracteres de uso privado passa
  por OCR. Evidência: `cmj/utils/genia/classificacao.py:193-202`,
  `cmj/utils/genia/extracao.py:17-44`.
- GENIA-CLA-005 [implementado] O prompt vem do campo `prompt` do tipo da matéria, em YAML lido com
  `yaml.safe_load`, com a lista `PROMPTs`. Vale o primeiro item com `status` verdadeiro, e a `mask`
  dele recebe o texto em `{context}`. Sem prompt, sem item ativo ou sem `mask`, nada é gerado. YAML
  com tags `!!python/*` não é lido e cai em GENIA-CLA-010. Evidência:
  `cmj/utils/genia/classificacao.py:159-191`, `sapl/materia/models.py:220`. Teste:
  `test_prompt_yaml_lido_com_safe_load`.
- GENIA-CLA-006 [implementado] Na ação `generate`, temperatura, `top_k` e `top_p` vêm do item do
  YAML, ou do padrão da classe. Na `generate_custom`, vêm da query string (ou dos kwargs de `run`,
  sem `request`). Os valores são convertidos para `float`, `int` e `float` na leitura. Valor inválido
  mostra erro e nada é gerado. Evidência: `cmj/utils/genia/classificacao.py:174-184`,
  `cmj/utils/genia/classificacao.py:214-221`. Testes:
  `test_generate_custom_converte_parametros_da_query_string`,
  `test_generate_custom_com_parametro_invalido_nao_gera`.

### Ações

- GENIA-CLA-007 [observado] Com `request`, a ação vem de `?ia_run=`. Sem `request`, vem do argumento
  `action`. O padrão é `generate`. Evidência: `cmj/utils/genia/classificacao.py:78-100`.
- GENIA-CLA-008 [implementado] A análise anterior só é substituída depois que a nova estiver pronta.
  A geração grava só a chave `genia` do `Metadata` do objeto e preserva as outras chaves. Se falhar,
  a análise anterior fica. Evidência: `cmj/utils/genia/classificacao.py:139-157`. Testes:
  `test_classificacao_substitui_so_a_chave_genia`,
  `test_classificacao_com_erro_mantem_analise_anterior`.
- GENIA-CLA-009 [implementado] A resposta precisa ser JSON. Ela é gravada em
  `Metadata.metadata["genia"]` com `model_name`, `template` (`table1`), `temperature`, `top_k` e
  `top_p`. Evidência: `cmj/utils/genia/classificacao.py:228-236`. Teste:
  `test_classificacao_usa_maior_cota_e_ignora_modelo_do_yaml`.
- GENIA-CLA-010 [implementado] Erros na geração são registrados em log e não sobem: `generate`
  devolve `None`. Sem cota, o usuário recebe o aviso (`warning`) "Nenhuma cota de I.A. disponível no
  momento. A análise anterior foi mantida. Tente novamente mais tarde." e o texto nem é extraído. Outros erros mostram
  "Ocorreu erro na geração da análise!". Evidência: `cmj/utils/genia/classificacao.py:241-253`.
  Testes: `test_classificacao_sem_cota_avisa_e_nao_extrai_texto`,
  `test_classificacao_com_erro_mantem_analise_anterior`.
- GENIA-CLA-011 [implementado] A ação `delete` remove só a chave `genia`. O `Metadata` que fica
  vazio é apagado. Com `request`, avisa "Análise removida com sucesso!". Evidência:
  `cmj/utils/genia/classificacao.py:112-124`. Teste: `test_delete_remove_so_a_chave_genia`.

### Quem chama

- GENIA-CLA-012 [observado] Na tela da matéria, `?ia_run=` só executa para quem tem
  `core.generate_analise_genia`. Os `temas` da análise viram `AssuntoMateria` e `MateriaAssunto`, e em
  seguida a análise de similaridade da matéria é disparada. Evidência:
  `sapl/materia/views.py:2940-2991`.
- GENIA-CLA-013 [observado] A task `task_classifica_materialegislativa` classifica uma matéria por
  execução, de 2024 ou anterior, e está desativada. Evidência: `sapl/base/tasks.py:56-125`.

## Decisões

- O `ia_model_name` que a migration não conseguir remover (GENIA-CLA-014) fica no YAML até ser
  editado à mão. Enquanto isso, é ignorado (GENIA-CLA-002).

## Fora do escopo

Templates que exibem a análise (`_templates/v2018/materia/materialegislativa_genia_table1.html`) e a
substituição de temas em `sapl/materia/forms.py`.
