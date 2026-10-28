# 1. Arquitetura do Chat RAG

## 1.1 Visão geral

O sistema tem **duas fases independentes**, ligadas apenas pela tabela `search_embedding`:

1. **Indexação (offline, assíncrona)** – disparada quando um Texto Articulado é *publicado*.
   Transforma dispositivos legais em *chunks* de texto, calcula tokens, `tsvector` e vetor semântico.
2. **Consulta (online, interativa)** – o usuário conversa via WebSocket; o LLM decide **quando e o que
   buscar** chamando uma *tool* (`buscar_na_base_dados`), que executa a recuperação híbrida e devolve
   o contexto que fundamenta a resposta.

> Diferente de um RAG "clássico" em que o backend sempre injeta o contexto no prompt, aqui o RAG é
> **agêntico**: o contexto só entra se o modelo chamar a função (até 10 chamadas automáticas por
> mensagem). A *system instruction* obriga o modelo a sempre usar a ferramenta.

## 1.2 Diagrama de componentes

```mermaid
flowchart LR
    subgraph Browser["Browser (Vue 3 - _frontend/v6)"]
        CM[ChatModule.vue]
        CS[ChatSessionView.vue]
        CH[ChatHistoryList.vue]
    end

    subgraph ASGI["Django Channels (ASGI)"]
        RT[routing.py<br/>ws/chat/&lt;session_id&gt;/]
        CC[ChatConsumer]
        RL[(Redis<br/>Channel Layer)]
    end

    subgraph Dominio["Regras de negócio"]
        CMG[ChatManager]
        IA[IAGenaiBase]
        SI[system instruction v3]
    end

    subgraph Dados["PostgreSQL + pgvector"]
        EMB[(search_embedding)]
        CSN[(ChatSession)]
        CMS[(ChatMessage)]
        QT[(IAQuota / IAQuotasLog)]
    end

    GEM[[Google Gemini API<br/>geração + embeddings + count_tokens]]

    CS <-- JSON/WebSocket --> RT --> CC
    CC <--> RL
    CC --> CMG
    CMG --> CSN & CMS
    CMG --> IA
    IA --> SI
    IA --> QT
    IA <--> GEM
    CMG -- "tool: buscar_na_base_dados" --> EMB
```

## 1.3 Fluxo de indexação (publicação de Texto Articulado)

```mermaid
sequenceDiagram
    autonumber
    participant V as sapl.compilacao.views (publicar: ?lock)
    participant C as Celery (fila cq_base)
    participant T as task_sync_embeddings_textoarticulado_function
    participant TA as TextoArticulado.generate_chunks
    participant DB as PostgreSQL
    participant G as Gemini API

    V->>C: apply_async([ta_id], countdown=5)
    C->>T: executa
    T->>DB: apaga embeddings de dispositivos substituídos / TAs revogados
    loop cada TextoArticulado
        T->>TA: generate_chunks()
        TA->>DB: cria/atualiza Embedding(chunk) + search_vector
        T->>G: count_tokens (para embeddings com total_tokens=0)
        T->>G: embed_content em lotes de 64 (1536 dim)
        T->>DB: grava vetor1536
    end
```

## 1.4 Fluxo de uma pergunta (online)

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuário (Vue)
    participant CC as ChatConsumer
    participant CM as ChatManager
    participant DB as PostgreSQL
    participant IA as IAGenaiBase
    participant G as Gemini
    participant R as Embedding.make_context

    U->>CC: {"message": "..."}
    CC->>CC: valida permissão, tamanho, escape HTML, normaliza espaços
    CC->>CM: process_user_message(session_id, msg, user)
    CM->>DB: salva ChatMessage(role=user) (aplica limites)
    CM->>DB: carrega histórico (sem a última msg do usuário)
    CM->>IA: chat_send_message(msg, history, tools=[buscar_na_base_dados])
    IA->>G: send_message (system instruction + tool)
    loop até 10 chamadas automáticas
        G-->>IA: function_call buscar_na_base_dados(query)
        IA->>CM: executa closure
        CM->>G: get_query_embedding(query) [1536 dim]
        CM->>R: make_context(query, embedding)
        R->>DB: busca vetorial (cosseno) + FTS + RRF
        R-->>CM: texto com "Fonte: [..](/ta/ID/text)"
        CM-->>G: function_response (contexto)
    end
    G-->>IA: texto final (Markdown)
    IA->>DB: IAQuotasLog.create_log() (peso 1)
    CM->>DB: salva ChatMessage(role=model, metadata.rag_results)
    CC-->>U: group_send → {"type":"chat_message","message":"... _(LLM: modelo)_"}
```

## 1.5 Mapa de responsabilidades

| Camada | Classe / função | Responsabilidade |
|--------|-----------------|------------------|
| Transporte | `ChatConsumer` | Autenticação/permissão, conexão única por sessão, validação e normalização da entrada, envio de respostas e erros |
| Aplicação | `ChatManager` | Limites (sessões/dia, mensagens/sessão), persistência de mensagens, título da sessão, histórico no formato Gemini, definição da *tool* de busca |
| Integração I.A. | `IAGenaiBase` | Cliente Gemini, configuração de geração, seleção de cota/modelo, `chats.create`, embeddings, contagem de tokens |
| Recuperação | `Embedding.make_context` | Busca híbrida (vetorial + FTS), fusão RRF, agrupamento por Texto Articulado, deduplicação e links de fonte |
| Indexação | `TextoArticulado.generate_chunks` + task Celery | Segmentação hierárquica dos dispositivos, persistência de chunks, embeddings |
| Persistência | `Embedding`, `ChatSession`, `ChatMessage`, `IAQuota` | Dados vetoriais, conversas e controle de consumo |
| Apresentação | `ChatSessionView.vue` | WebSocket, renderização das mensagens, tratamento do código `4001` |

## 1.6 Decisões de projeto relevantes

| Decisão | Motivo / efeito |
|---------|-----------------|
| **Chunk por dispositivo com hierarquia** (ancestrais + descendentes) | Cada chunk carrega o "caminho" jurídico (ex.: Lei › Capítulo › Artigo › Parágrafo), preservando contexto para o LLM |
| **Busca híbrida (semântica + FTS) com RRF** | Semântica captura sinônimos; FTS captura números de lei e termos exatos (ex.: "4353"); RRF combina rankings sem calibrar escalas |
| **`halfvec(1536)` + HNSW cosseno** | Metade da memória/índice de `vector(3072)`, com boa qualidade; Gemini permite reduzir dimensões na API |
| **Contexto agrupado por Texto Articulado e ordenado por `ordem`** | O LLM lê a norma em ordem natural, e não em ordem de similaridade aleatória |
| **Deduplicação de prefixos comuns** | Chunks vizinhos repetem ancestrais; a fusão evita repetir o mesmo cabeçalho e economiza tokens |
| **Links relativos `/ta/<id>/text`** | A resposta cita a fonte com link interno clicável; links externos são proibidos pela *system instruction* |
| **Cotas diárias por modelo (`IAQuota`)** | Controle de custo e rotação de modelos disponíveis |
| **Uma conexão ativa por sessão (código 4001)** | Evita respostas duplicadas e corridas na mesma conversa |

## 1.7 Dependências externas

* **PostgreSQL** com extensão `vector` (pgvector) e dicionário de FTS `portuguese`.
* **Redis**: broker do Celery e *channel layer* do Channels (`CHANNEL_LAYERS`).
* **Google Gemini API** (`google-genai`): geração, embeddings, `count_tokens`, listagem de modelos.
* **PyMuPDF** (`pymupdf`): usado em `_extract_pdf_text` (OCR de PDFs – fora do fluxo do chat, mas parte de `IAGenaiBase`).
* **BeautifulSoup** (`bs`): normalização de entidades HTML nos chunks.
