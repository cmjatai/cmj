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
| **Embeddings sem `vetor1536`** | **14.989 (21%)**, em 1.329 normas – invisíveis à busca semântica |
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

A baixa cobertura de Inciso/Parágrafo/Alinea/Item **é em grande parte o efeito dos 21% sem vetor**: a
linha existe, mas só aparece na busca textual.

## 7.2 O que foi corrigido

| Problema | Correção |
|----------|----------|
| Vetorização abortava no 1º erro e descartava o restante do lote/queryset | Retentativa com backoff, reprocesso individual do documento problemático, lista alinhada com `None`, interrupção só após lotes seguidos totalmente falhos; gravação por fatias de 256 ([02](./02-ingestao-e-indexacao.md#24-vetorização-e-tokens-embedding)) |
| Nada retomava pendentes (só republicar a norma) | Comando `sync_embeddings` ([02 §2.5](./02-ingestao-e-indexacao.md)) |
| Vetorização dependia de `total_tokens > 0` | Removida a dependência (tokens são informativos) |
| Anexo e Texto Não Estruturado fora do índice | Novos tipos individualizáveis com regras de qualidade (HTML→texto, mínimo de palavras, só TNU soltos) |
| FTS só com AND (3 termos não coexistentes → 0 resultados) | Camada OR de reserva + variantes de número ([03](./03-recuperacao-hibrida.md#2-busca-por-palavra-chave-fts--em-duas-camadas)) |

Efeito medido na busca textual (banco de produção, `top_k=60`):

| Consulta | Antes (AND) | Depois |
|----------|-------------|--------|
| incentivo empresa terraplenagem | 0 chunks | 60 chunks (39 artigos distintos) |
| diárias vereadores viagem | 16 chunks (10 artigos) | 60 chunks (42 artigos) – os 16 exatos vêm primeiro |
| licença maternidade servidora | 26 chunks | 60 chunks (40 artigos) |

## 7.3 Pendências conhecidas (não implementadas)

Problemas do algoritmo de chunking **atual** que continuam e que um `generate_chunks_v2` deve endereçar.
Todos medidos no backup:

| Achado | Medida |
|--------|--------|
| **Contaminação pela fronteira**: o primeiro dispositivo de nível ≤ ao atual (e mais um, se for Artigo) entra no chunk | 70% dos chunks de Artigo trazem outro(s) artigo(s) dentro (média de 0,71 a mais). Ex.: o chunk do Art. 1º contém o Art. 2º inteiro |
| **Redundância**: o texto aparece no próprio chunk, nos dos filhos (ancestral) e nos dos irmãos anteriores | Palavras nos chunks ≈ **2,1×** o texto único vigente |
| **Edição em cascata**: mudar o Art. 6º altera o chunk do Art. 5º (por causa da fronteira) | Reembedding sem mudança real de conteúdo |
| **Parágrafos sem o caput** (o pai é o Artigo, de `texto` vazio) | 96% dos chunks de parágrafo (385 de 399 na amostra) |
| Chunks com `<a href>` de referências cruzadas (`UrlizeReferencia`) | ~5% dos chunks com tags HTML |
| Limite em **palavras** (1536), não tokens | Praticamente nunca é atingido (p99 = 942 tokens) |
| FTS: camada OR sem ponderação por frequência (sem IDF) | Termos comuns encarecem a consulta (~1,7 s) |

Hipóteses **descartadas** pela medição: chunks grandes demais; ruído de dispositivos "(Revogado)" (0,1%);
ruído de "(Redação dada…)" (não aparece nos chunks); peso do prefixo da norma (8%).

### Próximo passo sugerido

1. Executar `sync_embeddings` em produção e medir novamente a fotografia de 7.1.
2. Montar um conjunto de ~50–100 perguntas reais com o artigo esperado e medir **recall@k/MRR** da
   estratégia atual.
3. Só então implementar o chunking v2 (unidade = Artigo completo, caput como cabeçalho dos parágrafos,
   contexto hierárquico no `title` do embedding, `metadata` estruturada) e comparar com o conjunto de
   perguntas antes de reindexar tudo.
