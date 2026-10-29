# 8. Avaliação da recuperação (`avaliar_rag`)

Como medir se uma mudança na recuperação (chunking, ranking, modelo de embedding) melhora ou piora o chat, antes
de reindexar e sem depender de impressão.

## 8.1 Conjunto de referência

[cmj/search/rag_eval/perguntas_referencia.json](../../cmj/search/rag_eval/perguntas_referencia.json): **57 perguntas**,
cada uma com o(s) artigo(s) que a respondem (`ta_id` + rótulo do artigo mais externo; `ordem` opcional desambigua
rótulos repetidos, como dois "Art. 153" no Código Tributário).

| Categoria | Perguntas | O que testa |
|-----------|-----------|-------------|
| `parafrase` | 17 | Linguagem do cidadão; o artigo usa outros termos |
| `contexto-da-norma` | 9 | O assunto está na ementa/nome da norma, não no texto do artigo |
| `termos-especificos` | 6 | Valores/nomes específicos (a busca textual deve ajudar) |
| `numero-da-norma` | 2 | Pergunta cita o número da lei/artigo |
| `alteracao` | 5 | Norma que acrescenta inciso/parágrafo/anexo a outra |
| `dispositivo-interno` | 11 | A resposta está num parágrafo/inciso que depende do caput |
| `artigo-longo` | 7 | Item específico dentro de um artigo com muitos incisos |

Foi elaborado sobre o banco de produção de out/2026 (os `ta_id` dependem dele): artigos sorteados de normas publicadas de
tipos variados, perguntas **parafraseadas** (sem copiar os termos do texto) e **sem dados pessoais** (portarias e decretos
de homenagem foram descartados). Um teste ([test_rag_eval.py](../../cmj/search/test_rag_eval.py)) valida a estrutura do
arquivo; o comando abaixo é a verificação contra os dados.

## 8.2 Métricas (por artigo)

Cada chunk recuperado é mapeado ao **artigo mais externo** que o contém; a lista de artigos distintos, na ordem de
relevância, é comparada com os esperados. Isso permite comparar estratégias com chunks diferentes em pé de igualdade.

- **hit@k** (k = 1, 3, 5, 10, 20): fração de perguntas com o artigo esperado entre os k primeiros;
- **MRR**: média de 1/posição do primeiro artigo esperado (0 se não aparece);
- **nao_encontradas**: perguntas sem o artigo esperado em `top_k`;
- **artigos_medio**: artigos distintos entre os `top_k` chunks (diversidade; a redundância do v1 reduz esse número).

## 8.3 O comando

```bash
# Linha de base da estratégia atual (somente leitura, sem API)
python manage.py avaliar_rag --estrategias v1 --detalhe

# Compara v1 × v2 SEM gravar nada: a v2 é gerada numa transação que é desfeita (~3 min)
python manage.py avaliar_rag --simular-v2 --rankers base n1 --detalhe

# Varia parâmetros da v2 simulada
python manage.py avaliar_rag --simular-v2 --estrategias v2 --rankers n1 --v2-max-tokens 250
python manage.py avaliar_rag --simular-v2 --estrategias v2 --rankers n1 --v2-sem-ementa

# Como o chat: busca semântica + textual (exige vetores nos chunks; chama a API do Gemini 1x por pergunta)
python manage.py avaliar_rag --modo hibrido --estrategias v2
```

Modos: `textual` (padrão; só Full-Text Search, não usa a API) e `hibrido` (RRF com a busca semântica, como no chat).
`--json-saida arquivo.json` grava métricas e resultados por pergunta.

## 8.4 Resultados (modo textual, banco de produção de out/2026)

v1 = chunking atual · v2 = por artigo (orçamento 350 tokens, ementa no cabeçalho) · `base` = `ts_rank` sem normalização ·
`n1` = normalização por log do tamanho.

| Métrica | v1/base | v1/n1 | v2/base | **v2/n1** |
|---------|--------:|------:|--------:|----------:|
| hit@1 | 0,246 | 0,316 | 0,386 | **0,474** |
| hit@5 | 0,544 | 0,544 | 0,632 | **0,702** |
| hit@20 | 0,649 | 0,754 | 0,754 | **0,789** |
| MRR | 0,357 | 0,448 | 0,502 | **0,583** |
| Não encontradas (de 57) | 17 | 13 | 11 | **10** |
| Artigos distintos no top 60 | 31,2 | 30,9 | 42,1 | **42,3** |

MRR por categoria (o ranker `n1` isolado em v1/n1 mostra o que é ganho do ranking e o que é ganho do chunking):

| Categoria (n) | v1/base | v1/n1 | **v2/n1** |
|---------------|--------:|------:|----------:|
| contexto-da-norma (9) | 0,074 | 0,265 | **0,607** |
| alteracao (5) | 0,155 | 0,462 | **0,700** |
| parafrase (17) | 0,205 | 0,315 | **0,480** |
| termos-especificos (6) | 0,440 | 0,468 | **0,673** |
| artigo-longo (7) | 0,475 | **0,607** | 0,586 |
| dispositivo-interno (11) | **0,846** | 0,768 | 0,717 |
| numero-da-norma (2) | **0,083** | 0,000 | 0,025 |

### Experimentos de parâmetros (v2, ranker `n1`)

| Configuração | hit@5 | hit@20 | MRR | Chunks | Tokens est. |
|--------------|------:|-------:|----:|-------:|------------:|
| orçamento 250 | 0,737 | 0,807 | 0,600 | 65,6 mil | 11,2 M |
| **orçamento 350** (adotado) | 0,702 | 0,789 | 0,583 | 48,1 mil | 8,5 M |
| orçamento 450 | 0,702 | 0,772 | 0,566 | 43,0 mil | 7,6 M |
| orçamento 600 | 0,702 | 0,789 | 0,554 | 40,2 mil | 7,2 M |
| 600 **sem ementa** | 0,649 | 0,719 | 0,536 | 40,2 mil | 7,2 M |
| 350 sem ementa | 0,632 | 0,737 | 0,558 | 48,1 mil | 8,5 M |

Rankers (v1 e v2, orçamento 600): `n1` foi o melhor nos dois (v2: MRR 0,563 contra 0,463 do `base`); `cd1` (cobertura de
densidade + log) ficou próximo; `n2` (divide pelo tamanho) e `cd2` foram claramente piores. Dar **peso menor ao cabeçalho**
no `tsvector` não teve efeito mensurável (MRR 0,563 × 0,565) e foi descartado por complexidade.

### Leitura dos resultados

- **O v2 é melhor no conjunto** (MRR +63%, hit@5 +16 p.p., menos perguntas sem resposta), com ~34% menos tokens.
- O ganho vem principalmente de **ementa no cabeçalho** (perguntas cujo assunto está no nome da norma) e de **artigos de
  normas que alteram outras** (o artigo-pai no cabeçalho diz qual lei é alterada).
- **O v1 ainda é melhor em "dispositivo-interno"**: um inciso isolado casa de forma muito específica com a pergunta.
  Orçamentos menores recuperam parte disso (MRR 0,756 com 250), ao custo de mais chunks.
- **Escolha do ranker é independente da estratégia**: `n1` melhorou também o v1 (MRR 0,357 → 0,448).

## 8.5 Limitações (leia antes de decidir)

- **Só o lado textual foi medido.** A busca semântica depende de vetores do `gemini-embedding-2` para os chunks v2, que
  ainda não existem (e a migração do v1 está em andamento). O resultado híbrido pode diferir, principalmente quanto ao
  orçamento de tokens (embeddings tendem a preferir trechos coerentes de tamanho médio).
- **57 perguntas**: cada uma vale ~1,75 ponto percentual; diferenças pequenas (ex.: 250 × 350 tokens) estão no ruído.
  Categorias com 2–7 perguntas (`numero-da-norma`, `alteracao`) são indicativas, não conclusivas.
- As perguntas foram escritas a partir dos mesmos textos do corpus (viés a favor de correspondência lexical) e por quem
  desenvolveu a avaliação. Perguntas reais dos usuários (tabela `ChatMessage`) devem complementá-las.
- **`numero-da-norma` não melhorou** (hit@5 = 0 em todas as variantes): a pergunta cita a lei e o artigo, mas todos os
  chunks da mesma lei empatam no número, e "artigo 75" não casa com o rótulo "Art. 75." no `tsvector`. Tratar isso exige
  reconhecer o padrão na consulta (ver [07](./07-diagnostico-e-evolucao.md#próximos-passos)).
