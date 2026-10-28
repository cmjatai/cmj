# 6. Operação, Limites e Pontos de Atenção

## 6.1 Pré-requisitos e configuração

| Item | Onde | Detalhe |
|------|------|---------|
| `GEMINI_API_KEY` | `cmj/settings/auth.py` (via `python-decouple` → `security.json`/env) | Obrigatória; sem ela o `genai.Client` falha |
| PostgreSQL + `pgvector` | Migrations de `cmj.search` | Extensão `vector` instalada; tipos `vector` e `halfvec` |
| Redis | `CHANNEL_LAYERS` (`channels_redis`) e `CELERY_BROKER_URL` | Necessário para WebSocket e para a task de indexação |
| Worker Celery | fila `cq_base` | Executa `task_sync_embeddings_textoarticulado` |
| ASGI | Channels | `search.routing.websocket_urlpatterns` precisa estar no roteador ASGI do projeto |
| Cota ativa | Admin → **Quotas IA** | Pelo menos uma `IAQuota` com `ativo=True`, `quota_diaria>0` e `IAGenaiBase` em *Serviços Autorizados* |
| Permissão | Admin → grupos/usuários | `search.can_use_chat_module` para quem pode usar o chat |

Bibliotecas Python: `google-genai`, `pgvector`, `channels`, `channels_redis`, `celery`, `beautifulsoup4`, `pymupdf`.

## 6.2 Limites de uso (usuários comuns)

| Limite | Valor | Mensagem exibida |
|--------|-------|------------------|
| Conversas novas por dia | 2 | "…o limite de conversas por usuário por dia foi atingido: (2)." |
| Mensagens por conversa (usuário + modelo) | 8 (= 4 perguntas) | "…o limite de mensagens por conversa foi atingido: (8)." |
| Tamanho da pergunta | 200 caracteres | "Mensagem muito longa. O limite é de 200 caracteres." |
| Chamadas de função por pergunta | 10 | (interno – `maximum_remote_calls`) |
| Cota diária de modelo | `IAQuota.quota_diaria` | "Nenhum Modelo com Quota para consumo disponível." |

Superusuários: sem limites de sessões/mensagens e com 10.000 caracteres por pergunta.

## 6.3 Checklist de troubleshooting

| Sintoma | Causas prováveis | Verificação |
|---------|------------------|-------------|
| Conexão WebSocket fecha imediatamente | Usuário anônimo ou sem `search.can_use_chat_module` | Permissões do usuário; log do Channels |
| Fecha com código **4001** | Mesma conversa aberta em outra aba | Esperado |
| Erro "Nenhum Modelo com Quota…" | Nenhuma `IAQuota` ativa, esgotada, ou sem `IAGenaiBase` autorizado | Admin Quotas IA; superusuário ao conectar sincroniza a lista de modelos |
| Resposta "informação não consta na base" para algo que existe | Norma não indexada (`vetor1536` NULL), norma revogada, chunk sem `search_vector`, *query* com termos demais (FTS AND) | Ver consultas abaixo; `metadata.rag_results.rag_query` da mensagem |
| Resposta com links quebrados/externos | *System instruction* alterada ou formato de `Fonte` modificado | Comparar com [§4.6](./04-chat-websocket-e-llm.md#46-system-instruction-v3) |
| Texto publicado não aparece no chat | Task Celery não executou (worker/fila `cq_base`), erro na API Gemini (apenas logado) | Logs do worker: "Starting task_sync_embeddings_textoarticulado_function…" |
| Embeddings sem vetor (`vetor1536` NULL) | Falha na API de embeddings (erro apenas logado; o lote parcial é gravado) | Reexecutar a task para o T.A. |

### Consultas úteis (shell Django)

```python
from cmj.search.models import Embedding, ChatMessage

# Pendências de indexação
Embedding.objects.filter(total_tokens=0).count()
Embedding.objects.filter(vetor1536__isnull=True).count()
Embedding.objects.filter(search_vector__isnull=True).count()

# Embeddings de um Texto Articulado
Embedding.objects.filter(dispositivo_set__ta_id=793).count()

# O que o LLM buscou na última resposta de uma conversa
m = ChatMessage.objects.filter(chat__session_id="...", role="model").last()
m.metadata["rag_results"]["rag_query"]
m.metadata["rag_results"]["rag_infos"]

# Reindexar um T.A.
from cmj.search.tasks import task_sync_embeddings_textoarticulado_function
task_sync_embeddings_textoarticulado_function([793])
```

## 6.4 Custos e consumo

* **Indexação:** 1 `count_tokens` por chunk novo + 1 chamada de embedding por lote de 64 chunks.
* **Pergunta:** 1 geração (+ até 10 ciclos de função) e, para cada chamada à *tool*, 1 chamada de embedding
  da consulta. O contexto retornado pode ser grande (até 60 chunks de até 1536 palavras antes da
  deduplicação), o que domina o custo de *prompt tokens* – acompanhe `rag_infos.prompt_token_count`.
* O log de cota é gravado **por mensagem do usuário** (peso 1), não por token.

## 6.5 Pontos de atenção

Os itens abaixo foram identificados na leitura inicial do código. Os marcados com ✅ já foram corrigidos
(testes em [cmj/search/test_chat_manager.py](../../cmj/search/test_chat_manager.py)).

### Segurança / privacidade

1. ✅ **Propriedade da sessão.** `ChatManager.add_message_to_context` agora recusa (`PermissionError`) uma
   sessão existente de outro usuário; `get_context_for_gemini(session_id, user=…)` filtra pelo dono; e o
   `ChatConsumer.connect` fecha a conexão **antes** de derrubar conexões antigas (o `ChatSession.session_id`
   continua sendo único globalmente). O ID gerado pelo frontend (`Math.random()`, em `ChatHistoryList.vue`)
   segue curto e não criptográfico – a verificação de dono é o que protege, não o sigilo do ID.
2. ✅ **Mensagens de erro.** Só `ValueError` (limites de uso) e `IAQuotaUnavailableError` (sem cota) são
   enviados ao cliente; qualquer outra exceção é registrada com `logger.exception` e o usuário recebe uma
   mensagem genérica.
3. A entrada do usuário continua **escapada com `html.escape`** *antes* de ser salva e enviada ao LLM
   (entidades como `&amp;` entram no prompt e no histórico) – mantido por proteger a renderização no
   frontend. O limite de 200 caracteres é validado antes do escape.

### Correção funcional

4. ✅ **Chat do `genai` sem estado por conexão.** `IAGenaiBase.chat_send_message` agora cria um `Chat` por
   mensagem, a partir do histórico do banco. Assim a *closure* de `buscar_na_base_dados` e a lista
   `rag_query` pertencem sempre à mensagem corrente (`metadata.rag_results.rag_query` correto em todas as
   respostas), e modelo/cota são escolhidos e registrados a cada mensagem. Contrapartida: as chamadas de
   função de turnos anteriores não fazem parte do histórico reenviado (apenas texto).
5. ✅ **Falha após salvar a pergunta.** Se a I.A. falhar, `process_user_message` remove a pergunta recém-salva
   e relança a exceção: não sobra mensagem órfã, não conta no limite de 8 e não há `user` consecutivos.
6. ✅ **Ordem de comparação em `generate_chunks`.** A comparação com os chunks salvos usa
   `d.embeddings.order_by("id")` (a ordenação padrão `-id` invertia a ordem em dispositivos com vários chunks).
7. ✅ **Chunk vazio.** O laço de divisão só fecha um chunk se ele tiver conteúdo.
8. ✅ **`total_tokens=0` por falha de API** não impede mais a vetorização: a task seleciona todo embedding
   com `vetor1536` nulo. (A contagem de tokens é apenas informativa.)
9. **FTS com AND** (`plainto_tsquery`): consultas longas reduzem a recuperação textual; a mitigação está
   no prompt (palavras-chave curtas e múltiplas tentativas). Mantido como decisão de projeto.

### Manutenção

10. ✅ `print` de depuração removido de `chat_send_message`.
11. ✅ Código morto removido da task (após `continue`) e de `generate_chunks` (`if False:`).
12. ✅ `make_context__old` e `make_context__20260225` removidos (sem chamadores).
13. `Embedding.vetor` (3072) permanece como campo legado (remoção exige migration) e `prepare_query` não é
    utilizado.
14. ✅ Docstrings de `Embedding` corrigidas: o modelo efetivo é `gemini-embedding-2`, 1536 dimensões.

## 6.6 Como evoluir com segurança

| Mudança | O que revisar |
|---------|---------------|
| Trocar o modelo de embedding / dimensão | `get_query_embedding`, `embed_documents`, `HalfVectorField`, índice HNSW (migration), **reindexar tudo** |
| Alterar `chunk_size` ou tipos individualizáveis | `generate_chunks`; a comparação por conteúdo recriará os chunks afetados; custo de reembedding |
| Mudar o formato `Fonte:` | `make_context` **e** *system instruction* (Bloco 1, item 3) |
| Indexar outros modelos (além de `Dispositivo`) | `make_context` assume `content_object.ta_id` e `.ordem`; objetos sem `ta_id` são ignorados |
| Ajustar relevância | `top_k`, `RRF_K`, parâmetros HNSW (`ef_search` em tempo de consulta), tipo de `SearchQuery` (`websearch`/`raw`) |
| Novo serviço de I.A. com cota | Adicionar em `IAQuota.ServicosAutorizados` e autorizar o nome da classe |
| Novo tipo de mensagem WebSocket | `ChatConsumer` **e** `handleSocketMessage` em `ChatSessionView.vue` |
