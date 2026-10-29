# 8. Avaliação da recuperação (`avaliar_rag`)

Como medir se uma mudança na recuperação (chunking, ranking, modelo de embedding) melhora ou piora o chat, antes
de reindexar e sem depender de impressão.

## 8.1 Conjunto de referência

[cmj/search/rag_eval/perguntas_referencia.json](../../cmj/search/rag_eval/perguntas_referencia.json): **93 perguntas**,
cada uma com o(s) artigo(s) que a respondem (`ta_id` + rótulo do artigo mais externo; `ordem` opcional desambigua
rótulos repetidos, comum no Código Tributário, que tem dois "Art. 153", dois "Art. 175" etc.).

| Categoria | Perguntas | O que testa |
|-----------|-----------|-------------|
| `parafrase` | 51 | Linguagem do cidadão; o artigo usa outros termos |
| `contexto-da-norma` | 9 | O assunto está na ementa/nome da norma, não no texto do artigo |
| `termos-especificos` | 9 | Valores/nomes específicos (a busca textual deve ajudar) |
| `numero-da-norma` | 3 | Pergunta cita o número da lei/artigo |
| `alteracao` | 5 | Norma que acrescenta inciso/parágrafo/anexo a outra |
| `dispositivo-interno` | 11 | A resposta está num parágrafo/inciso que depende do caput |
| `artigo-longo` | 5 | Item específico dentro de um artigo com muitos incisos |

**Por porte da norma** (nº de artigos vigentes; calculado automaticamente): pequena (<10) 15 · média (10–49) 21 ·
grande (50–199) 23 · **muito grande (≥200) 34**. Só 4 normas têm ≥200 artigos (Código Tributário 458, Estatuto dos
Servidores 372, Estatuto do Magistério 222, Lei Orgânica 221) e são as mais consultadas e as mais difíceis, porque muitos
artigos parecidos competem entre si. O conjunto inicial (57 perguntas) tinha só 3 delas; as demais foram acrescentadas
depois de uma revisão (ver [§8.5](#85-limitações-leia-antes-de-decidir)). O corpus real é o oposto: 94% das normas são
pequenas (60% dos artigos).

Foi elaborado sobre o banco de produção de out/2026 (os `ta_id` dependem dele): artigos sorteados de normas publicadas de
tipos variados, perguntas **parafraseadas** (sem copiar os termos do texto) e **sem dados pessoais** (portarias e decretos
de homenagem foram descartados). O comando **recusa** perguntas cuja norma esperada esteja revogada ou não publicada
(nenhuma estratégia a indexa; seriam "não encontradas" por construção). Um teste
([test_rag_eval.py](../../cmj/search/test_rag_eval.py)) valida a estrutura do arquivo.

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
| hit@1 | 0,172 | 0,237 | 0,441 | **0,473** |
| hit@5 | 0,538 | 0,527 | 0,677 | **0,677** |
| hit@20 | 0,688 | 0,774 | 0,828 | **0,860** |
| MRR | 0,327 | 0,392 | 0,556 | **0,579** |
| Não encontradas (de 93) | 23 | 19 | 10 | **9** |
| Artigos distintos no top 60 | 31,5 | 32,0 | 43,7 | **44,2** |

No nível da pergunta (v1/n1 × v2/n1): o v2 foi melhor em **50**, pior em **14** e igual em **29** das 93.

### Por porte da norma

O resultado geral é dominado por normas pequenas e médias, que são a maioria do corpus. Como as **normas grandes são as mais
consultadas**, a estratificação é a leitura que importa:

| Porte (perguntas) | hit@5 v1/n1 → v2/n1 | hit@20 v1/n1 → v2/n1 | MRR v1/n1 → v2/n1 |
|-------------------|--------------------:|---------------------:|------------------:|
| pequena <10 art. (15) | 0,53 → 0,73 | 0,80 → 0,80 | 0,49 → 0,59 |
| média 10–49 (21) | 0,67 → 0,76 | 0,81 → 0,90 | 0,54 → 0,69 |
| grande 50–199 (23) | 0,57 → 0,65 | 0,78 → 0,87 | 0,37 → 0,54 |
| **muito grande ≥200 (34)** | **0,41 → 0,62** | **0,74 → 0,85** | **0,28 → 0,54** |

O ganho do v2 é **maior** nas normas muito grandes. Mesmo assim, 38% das perguntas dessas normas ficam fora do top 5 (v2):
é onde há mais espaço para melhorar (ver limitações).

MRR por categoria (o ranker `n1` isolado em v1/n1 mostra o que é ganho do ranking e o que é ganho do chunking):

| Categoria (n) | v1/base | v1/n1 | **v2/n1** |
|---------------|--------:|------:|----------:|
| contexto-da-norma (9) | 0,074 | 0,265 | **0,607** |
| alteracao (5) | 0,155 | 0,462 | **0,700** |
| termos-especificos (9) | 0,413 | 0,456 | **0,782** |
| parafrase (51) | 0,245 | 0,293 | **0,506** |
| artigo-longo (5) | 0,665 | **0,850** | 0,820 |
| dispositivo-interno (11) | **0,846** | 0,768 | 0,717 |
| numero-da-norma (3) | **0,056** | 0,022 | 0,017 |

### Experimentos de parâmetros (v2, ranker `n1`, 93 perguntas)

| Configuração | hit@5 | hit@20 | MRR | MRR "muito grande" | Chunks | Tokens est. |
|--------------|------:|-------:|----:|-------------------:|-------:|------------:|
| orçamento 250 | 0,699 | 0,849 | 0,607 | 0,567 | 65,6 mil | 11,2 M |
| **orçamento 350** (adotado) | 0,677 | 0,860 | 0,579 | 0,536 | 48,1 mil | 8,5 M |
| orçamento 600 | 0,667 | 0,839 | 0,562 | 0,540 | 40,2 mil | 7,2 M |
| 350 **sem ementa** | 0,634 | 0,785 | 0,539 | 0,453 | 48,1 mil | 8,5 M |

(Chunks e tokens: contagens anteriores à regra de estruturas revogadas, que reduz um pouco o total.)

Rankers (v1 e v2): `n1` foi o melhor nos dois; `cd1` (cobertura de densidade + log) ficou próximo; `n2` (divide pelo
tamanho) e `cd2` foram claramente piores. Dar **peso menor ao cabeçalho** no `tsvector` não teve efeito mensurável e foi
descartado por complexidade. (Esses dois experimentos foram feitos no conjunto inicial de 57 perguntas.)

### Leitura dos resultados

- **O v2 é melhor no conjunto** (MRR 0,39 → 0,58; perguntas sem resposta 19 → 9), com ~34% menos tokens, **e o ganho se
  mantém, maior, nas normas muito grandes**.
- O ganho vem principalmente de **ementa no cabeçalho** (sem ela, "muito grande" cai de 0,536 para 0,453 de MRR) e de
  **artigos de normas que alteram outras** (o artigo-pai no cabeçalho diz qual lei é alterada).
- **O v1 ainda é melhor em "dispositivo-interno"**: um inciso isolado casa de forma muito específica com a pergunta.
- **A escolha do ranker é independente da estratégia**: `n1` melhorou também o v1 (MRR 0,327 → 0,392).
- O que sobra nas normas grandes é, em geral, **distância de vocabulário** (ex.: "reeleito" × "reeleição", "perde o direito de
  pedir de volta" × "pleitear a restituição"), que a busca textual não resolve e a semântica deve ajudar: ver limitações.

## 8.5 Limitações (leia antes de decidir)

- **Só o lado textual foi medido.** A busca semântica depende de vetores do `gemini-embedding-2` para os chunks v2, que
  ainda não existem (e a migração do v1 está em andamento). O resultado híbrido pode diferir, principalmente quanto ao
  orçamento de tokens (embeddings tendem a preferir trechos coerentes de tamanho médio) e nas normas grandes, onde a
  distância de vocabulário pesa mais.
- **93 perguntas**: cada uma vale ~1,1 ponto percentual; diferenças pequenas (ex.: 250 × 350 tokens) estão no ruído.
  Categorias e portes com poucas perguntas (`numero-da-norma`, `alteracao`, `pequena`) são indicativos, não conclusivos.
- As perguntas foram escritas a partir dos mesmos textos do corpus (viés a favor de correspondência lexical) e por quem
  desenvolveu a avaliação. Perguntas reais dos usuários (tabela `ChatMessage`) devem complementá-las.
- **Armadilhas encontradas ao revisar a própria avaliação** (e por que existem a estratificação e a validação):
  1. A primeira versão tinha só 3 perguntas das 4 normas com ≥200 artigos; uma métrica agregada escondia o desempenho
     nas normas mais importantes. Por isso o comando passou a reportar **por porte**.
  2. 5 perguntas apontavam para normas **revogadas** (nenhuma estratégia as indexa); o comando agora as recusa.
  3. A estratificação também expôs um **bug da própria v2** (uma regra nova tratava "Livro" com texto vazio como revogado e
     descartava ~28% do Código Tributário): sem a estratificação, o resultado geral quase não mudaria e o bug passaria.
     Há teste de regressão (`test_estrutura_com_texto_vazio_nao_e_revogada`).
- **`numero-da-norma` não melhorou** (hit@5 = 0 em todas as variantes): a pergunta cita a lei e o artigo, mas todos os
  chunks da mesma lei empatam no número, e "artigo 75" não casa com o rótulo "Art. 75." no `tsvector`. Tratar isso exige
  reconhecer o padrão na consulta (ver [07](./07-diagnostico-e-evolucao.md#próximos-passos)).
