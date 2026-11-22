# Genia: embeddings

Status: implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/embeddings.py`, `cmj/search/models.py`
Testes: `cmj/utils/genia/test_genia.py`, `cmj/search/test_embeddings.py`

## Escopo

`IAEmbeddingService`: vetorização de documentos e de consultas para a busca semântica. Ingestão e
recuperação estão em `docs/tutorials/rag/02-ingestao-e-indexacao.md` e
`docs/tutorials/rag/03-recuperacao-hibrida.md`.

## Regras

- GENIA-EMB-001 [implementado] A consulta é vetorizada com o modelo `gemini-embedding-2`, em 1536
  dimensões, no formato `task: question answering | query: <texto>`. Com `is_qa_mode=False`, a tarefa
  é `search result`. Evidência: `cmj/utils/genia/embeddings.py:31-49`.
- GENIA-EMB-002 [implementado] Cada documento é enviado como `title: <título> | text: <texto>`. Sem
  título, usa `none`. Evidência: `cmj/utils/genia/embeddings.py:26-29`.
- GENIA-EMB-003 [observado] Os documentos seguem em lotes de 64. Cada lote é tentado até 3 vezes, com
  espera de 2 e 4 segundos. Resposta com quantidade de vetores diferente da de textos conta como
  falha. Evidência: `cmj/utils/genia/embeddings.py:51-76`. Teste:
  `test_embed_documents_repete_em_falha_transitoria`.
- GENIA-EMB-004 [observado] Se o lote falhar nas 3 tentativas, cada documento é enviado sozinho, uma
  vez. O que falhar fica como `None` na posição correspondente da lista. Evidência:
  `cmj/utils/genia/embeddings.py:100-116`. Teste: `test_embed_documents_isola_documento_problematico`.
- GENIA-EMB-005 [observado] Dois lotes seguidos sem nenhum vetor interrompem o processamento, e a
  lista devolvida fica menor que a de entrada. Evidência: `cmj/utils/genia/embeddings.py:120-128`.
  Teste: `test_embed_documents_interrompe_quando_api_fora_do_ar`.
- GENIA-EMB-006 [implementado] O serviço é isento de cota por decisão: não consulta nem registra `IAQuota`.
  Evidência: `cmj/utils/genia/embeddings.py:18`.
- GENIA-EMB-007 [observado] A contagem de tokens de um chunk usa o modelo padrão da classe-base
  (`gemini-3.5-flash-lite`), não o modelo de embedding. Evidência: `cmj/search/models.py:142`,
  `cmj/utils/genia/base.py:36`.

## Decisões

- O serviço não tem cota nem registro de consumo, e isso é intencional (GENIA-EMB-006). A execução
  do modelo de embedding é livre, dentro do que a ingestão já implementa: lotes, repetição e
  interrupção por API fora do ar.
- Restrição: a dimensão 1536 está fixa no serviço e em `Embedding.vetor1536`. Trocar a dimensão exige
  reindexar toda a base. O modelo `gemini-embedding-2` não deve ser substituído enquanto a biblioteca
  `google.genai` o fornecer.
- A contagem de tokens de um chunk (GENIA-EMB-007) usa outro modelo e serve só como estimativa.

## Fora do escopo

Geração de chunks, busca por `tsvector` e ranqueamento.
