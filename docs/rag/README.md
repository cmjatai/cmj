# CHAT RAG do Portal CMJ

Documentação do **Chat com I.A. baseado em RAG** (*Retrieval-Augmented Generation*) do portal da
Câmara Municipal de Jataí. O chat responde perguntas jurídicas **exclusivamente** a partir do
conteúdo dos Textos Articulados (leis, decretos, resoluções etc.) publicados no sistema.

## Índice

| # | Documento | Conteúdo |
|---|-----------|----------|
| 1 | [01-arquitetura.md](./01-arquitetura.md) | Visão geral, componentes, diagramas e mapa de arquivos |
| 2 | [02-ingestao-e-indexacao.md](./02-ingestao-e-indexacao.md) | Como os textos viram chunks, embeddings e `tsvector` (pipeline offline) |
| 3 | [03-recuperacao-hibrida.md](./03-recuperacao-hibrida.md) | `Embedding.make_context`: busca vetorial + FTS + RRF e montagem do contexto |
| 4 | [04-chat-websocket-e-llm.md](./04-chat-websocket-e-llm.md) | `ChatConsumer`, `ChatManager`, `IAGenaiBase`, function calling, system instruction e cotas |
| 5 | [05-modelos-de-dados.md](./05-modelos-de-dados.md) | `Embedding`, `ChatSession`, `ChatMessage`, `IAQuota`, índices e metadados salvos |
| 6 | [06-operacao-limites-e-pontos-de-atencao.md](./06-operacao-limites-e-pontos-de-atencao.md) | Configuração, permissões, limites, troubleshooting e pontos de atenção do código atual |
| 7 | [07-diagnostico-e-evolucao.md](./07-diagnostico-e-evolucao.md) | Medições do índice de produção, correções de cobertura/full-text, problemas do chunking v1 e roteiro de adoção do v2 |
| 8 | [08-avaliacao-da-recuperacao.md](./08-avaliacao-da-recuperacao.md) | Conjunto de 57 perguntas de referência, comando `avaliar_rag`, métricas, resultados v1 × v2 e limitações |

## Resumo em 30 segundos

```text
PUBLICAÇÃO (offline)                              CONVERSA (online)
────────────────────                              ─────────────────
TextoArticulado publicado                         Usuário (Vue v6) ──WebSocket──▶ ChatConsumer
   │ (lock)                                                                          │
   ▼                                                                                 ▼
task Celery cq_base                                                              ChatManager
   │                                                                                 │ histórico + limites
   ▼                                                                                 ▼
TextoArticulado.generate_chunks()                                              IAGenaiBase (Gemini)
   │  chunks (≤1536 palavras)                                                        │ function calling
   ▼                                                                                 ▼
Embedding.chunk ─▶ tsvector (portuguese)                                  buscar_na_base_dados(query)
   │                                                                                 │
   ▼                                                                                 ▼
gemini-embedding-2 (1536 dim) ─▶ vetor1536 ──────────────▶ Embedding.make_context (pgvector + FTS + RRF)
                                                                                     │
                                                          texto com "Fonte: [link]" ◀┘ → LLM → resposta Markdown
```

* **Modelo de geração:** `gemini-3-flash-preview` (padrão) – ou o modelo escolhido via `IAQuota`.
* **Modelo de embedding:** `gemini-embedding-2`, saída reduzida para **1536 dimensões** (`halfvec`).
* **Banco:** PostgreSQL + `pgvector` (índice HNSW, cosseno) + Full-Text Search (`portuguese`, índice GIN).
* **Transporte:** Django Channels (WebSocket `/ws/chat/<session_id>/`) com Redis como channel layer.
* **Frontend:** `_frontend/v6/src/modules/chat/` (Vue 3).

## Arquivos-fonte principais

| Arquivo | Papel |
|---------|-------|
| [cmj/search/models.py](../../cmj/search/models.py) | `Embedding` (+ `make_context`), `ChatSession`, `ChatMessage` |
| [cmj/search/consumers.py](../../cmj/search/consumers.py) | `ChatConsumer` (WebSocket) |
| [cmj/search/chat_manager.py](../../cmj/search/chat_manager.py) | `ChatManager` (regras de negócio do chat e ponte com a I.A.) |
| [cmj/utils/genia/\_\_init\_\_.py](../../cmj/utils/genia/__init__.py) | `IAGenaiBase` (cliente Gemini, chat, embeddings, cotas) |
| [cmj/utils/genia/genia_system_instruction_v3.py](../../cmj/utils/genia/genia_system_instruction_v3.py) | *System instruction* do RAG |
| [cmj/search/routing.py](../../cmj/search/routing.py) | Rota WebSocket |
| [cmj/search/tasks.py](../../cmj/search/tasks.py) | Task de sincronização de embeddings |
| [sapl/compilacao/models.py](../../sapl/compilacao/models.py) | `TextoArticulado.generate_chunks` e `Dispositivo.embeddings` |
| [cmj/core/models.py](../../cmj/core/models.py) | `IAQuota` / `IAQuotasLog` |
