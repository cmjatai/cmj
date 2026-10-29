# 7. Diagnóstico do índice e evolução

Medições feitas sobre um **backup do banco de produção** (71.697 embeddings, 5.768 normas) em
outubro/2026. O backup pode misturar versões antigas do algoritmo de chunking (há embeddings de tipos que o
código atual não gera), então os números descrevem o índice **existente**, não apenas o que o código atual
produziria.

## 7.1 Fotografia do índice (antes das correções de cobertura)

| Métrica | Valor |
|---------|-------|
| Embeddings | 71.697 (todos de `Dispositivo`) |
| Tokens por chunk | mediana 133 · p90 279 · p99 942 · máx. 14.339 |
| Chunks > 500 tokens | 2.244 (3%) · > 1.000 tokens: 670 |
| Tipos com mais chunks | Artigo 28.220 · Inciso 17.522 · Parágrafo 10.136 · Ementa 5.752 · Item 5.369 · Alinea 4.382 |
| Chunks por dispositivo | 99,5% têm exatamente 1 |
| **Embeddings sem `vetor1536`** | **14.989 (21%)**, em 1.329 normas – invisíveis à busca semântica. **Não é falha:** é a migração em andamento de `gemini-embedding-001` para `gemini-embedding-2` (o campo foi limpo e está sendo regerado em blocos) |
| Sem `search_vector` | 8 |
| Duplicatas textuais exatas | 433 registros extras (0,6%) |
| Prefixo com o nome da norma | ~48 caracteres, 8% do texto |

### Cobertura por tipo de dispositivo (vigentes)

| Tipo | Dispositivos | Com embedding | Observação |
|------|-------------:|--------------:|-----------|
| Caput | 31.159 | 0% | Intencional: entra no chunk do Artigo/Incisos |
| Item | 7.742 | 69% | |
| Inciso | 20.917 | 84% | |
| Parágrafo | 12.843 | 79% | |
| Ementa | 5.959 | 97% | |
| Alinea | 5.625 | 78% | |
| **Texto Não Estruturado** | 5.056 | 1% | 2.157 normas; 5.035 com texto, mas só 490 têm > 40 palavras (o resto é fecho/assinatura) |
| **Anexo** | 175 | 0% | |
| Normas sem nenhum embedding | 213 (187 publicadas) | | |

A baixa cobertura de Inciso/Parágrafo/Alinea/Item **é em grande parte o efeito dos 21% ainda sem vetor** (migração
de modelo de embedding em andamento): a linha existe, mas só aparece na busca textual até ser vetorizada.
`python manage.py sync_embeddings` conclui essa migração (é retomável).

## 7.2 O que foi corrigido

| Problema | Correção |
|----------|----------|
| Vetorização abortava no 1º erro e descartava o restante do lote/queryset | Retentativa com backoff, reprocesso individual do documento problemático, lista alinhada com `None`, interrupção só após lotes seguidos totalmente falhos; gravação por fatias de 256 ([02](./02-ingestao-e-indexacao.md#24-vetorização-e-tokens-embedding)) |
| Sem forma de retomar a vetorização em massa (só republicando a norma) | Comando `sync_embeddings` ([02 §2.5](./02-ingestao-e-indexacao.md)) |
| Vetorização dependia de `total_tokens > 0` | Removida a dependência (tokens são informativos) |
| Anexo e Texto Não Estruturado fora do índice | Novos tipos individualizáveis com regras de qualidade (HTML→texto, mínimo de palavras, só TNU soltos) |
| FTS só com AND (3 termos não coexistentes → 0 resultados) | Camada OR de reserva + variantes de número ([03](./03-recuperacao-hibrida.md#2-busca-por-palavra-chave-fts--em-duas-camadas)) |
| Desempate do ranking textual dependia do plano do PostgreSQL (resultados mudavam entre execuções) | `ORDER BY rank DESC, id` – determinístico |
| `ts_rank` sem normalização favorecia chunks longos que repetem os termos | Ranker `n1` (divide pelo log do tamanho) como padrão: ver [08](./08-avaliacao-da-recuperacao.md) |

Efeito medido na busca textual (banco de produção, `top_k=60`):

| Consulta | Antes (AND) | Depois |
|----------|-------------|--------|
| incentivo empresa terraplenagem | 0 chunks | 60 chunks (39 artigos distintos) |
| diárias vereadores viagem | 16 chunks (10 artigos) | 60 chunks (42 artigos) – os 16 exatos vêm primeiro |
| licença maternidade servidora | 26 chunks | 60 chunks (40 artigos) |

## 7.3 Problemas do chunking v1 e como o v2 os trata

Medidos no backup de produção; o chunking v2 ([02 §2.6](./02-ingestao-e-indexacao.md#26-chunking-v2-por-artigo)) endereça cada um:

| Achado no v1 | Medida | No v2 |
|--------------|--------|-------|
| **Contaminação pela fronteira**: o primeiro dispositivo de nível ≤ ao atual (e mais um, se for Artigo) entra no chunk | 70% dos chunks de Artigo trazem outro(s) artigo(s) dentro (média de 0,71 a mais). Ex.: o chunk do Art. 1º contém o Art. 2º inteiro | A unidade é o Artigo completo; não há janela de vizinhos |
| **Redundância**: o texto aparece no próprio chunk, nos dos filhos (ancestral) e nos dos irmãos anteriores | Palavras nos chunks ≈ **2,1×** o texto único vigente | Um chunk por artigo (divide só acima do orçamento); ~34% menos tokens (8,5 M × 12,7 M) |
| **Edição em cascata**: mudar o Art. 6º altera o chunk do Art. 5º | Reembedding sem mudança real de conteúdo | Sincronização por hash: só o chunk alterado é recriado |
| **Parágrafos sem o caput** (o pai é o Artigo, de `texto` vazio) | 96% dos chunks de parágrafo (385 de 399 na amostra) | Parágrafos ficam dentro do chunk do artigo, com o caput |
| Assunto só na ementa da norma | Categoria "contexto-da-norma": MRR 0,07 no v1 | Ementa (truncada) no cabeçalho de cada chunk: MRR 0,61 |
| Chunks com `<a href>` de referências cruzadas (`UrlizeReferencia`) | ~5% dos chunks com tags HTML | Texto puro em todos os chunks |
| Limite em **palavras** (1536), não tokens | Praticamente nunca é atingido (p99 = 942 tokens) | Orçamento em tokens estimados (350) |

Pendência que continua: a camada OR do FTS não pondera por frequência (sem IDF); termos comuns encarecem a
consulta (~1,7 s).

Hipóteses **descartadas** pela medição: chunks grandes demais; ruído de dispositivos "(Revogado)" (0,1%);
ruído de "(Redação dada…)" (não aparece nos chunks); peso do prefixo da norma (8%); dar peso menor ao
cabeçalho no `tsvector` (sem efeito mensurável, ver [08](./08-avaliacao-da-recuperacao.md)).

## 7.4 Como adotar o v2

A v2 convive com a v1 na mesma tabela (`metadata.chunk_strategy = "v2"`; a v1 não tem a chave). Nada muda em
produção enquanto `RAG_CHUNK_STRATEGY` for `v1` (padrão).

1. Gerar a v2 sem afetar o chat: `python manage.py sync_embeddings --estrategia v2 --todos-publicados --sem-pendentes`
   cria os chunks v2 (com `search_vector` e sem vetor; ~3 min para as ~5,9 mil normas).
2. Vetorizar: `python manage.py sync_embeddings --estrategia v2` – **consome a API** (~8,5 M tokens de entrada).
3. Avaliar com a API (modo `hibrido`) v1 × v2 ([08](./08-avaliacao-da-recuperacao.md)).
4. Se aprovado, definir `RAG_CHUNK_STRATEGY=v2` (variável de ambiente). O chat e a task passam a usar só a v2.
5. Remover a v1: `Embedding.objects.exclude(metadata__chunk_strategy="v2").delete()`. Manter as duas por muito
   tempo faz o HNSW filtrar por estratégia depois da busca aproximada (menos resultados por consulta).

### Próximos passos

1. Rodar a avaliação em modo `hibrido` depois de vetorizar a v2 (a avaliação feita aqui foi só textual).
2. Ampliar o conjunto de perguntas com perguntas reais dos usuários do chat (ver `ChatMessage`).
3. Perguntas por número ("artigo 75 da lei 2281") não melhoraram: reconhecer o padrão "art. N / lei N" na
   consulta e filtrar por norma/rótulo.
