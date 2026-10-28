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
| Resposta "informação não consta na base" para algo que existe | Norma não indexada (`vetor1536` NULL / `total_tokens` 0), norma revogada, chunk sem `search_vector`, *query* com termos demais (FTS AND) | Ver consultas abaixo; `metadata.rag_results.rag_query` da mensagem |
| Resposta com links quebrados/externos | *System instruction* alterada ou formato de `Fonte` modificado | Comparar com [§4.6](./04-chat-websocket-e-llm.md#46-system-instruction-v3) |
| Texto publicado não aparece no chat | Task Celery não executou (worker/fila `cq_base`), erro na API Gemini (apenas logado) | Logs do worker: "Starting task_sync_embeddings_textoarticulado_function…" |
| Embeddings com `total_tokens=0` que nunca recebem vetor | `count_tokens` falhou (retorna 0) e a task só vetoriza `total_tokens>0` | Reexecutar a task para o T.A. |

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

## 6.5 Pontos de atenção observados no código atual

Itens verificados na leitura do código; não alteram o funcionamento descrito, mas merecem avaliação.

### Segurança / privacidade

1. **Propriedade da sessão não é verificada.** `ChatManager.add_message_to_context` faz
   `ChatSession.get_or_create(session_id=…, defaults={"user": user})`, e o `ChatConsumer` entra no grupo e
   carrega o histórico apenas pelo `session_id` (único global). Quem conhecer/adivinhar o `session_id` de
   outro usuário e tiver a permissão do chat poderia **ler o histórico e escrever na conversa**. Mitigação
   atual: o frontend gera o ID com `'session_' + Math.random().toString(36).substr(2, 9)`
   (`ChatHistoryList.vue`), que **não é criptograficamente seguro** e é curto. Recomenda-se validar
   `chat_session.user == user` no consumer e no `ChatManager`.
2. **Mensagens de erro brutas** (`str(e)`) são enviadas ao cliente – útil para limites, mas pode expor
   detalhes internos de exceções inesperadas.
3. A entrada do usuário é **escapada com `html.escape`** *antes* de ser salva e enviada ao LLM (entidades como
   `&amp;` entram no prompt e no histórico). O limite de 200 caracteres é validado antes do escape.

### Correção funcional

4. **Estado do `genai` Chat por conexão.** `IAGenaiBase._chat` é criado na **primeira** mensagem de cada
   conexão WebSocket e reutilizado nas seguintes (o `history` do banco só é usado na criação). Efeitos:
   * a *closure* `buscar_na_base_dados` e a lista `rag_query` ficam presas à **primeira** mensagem; nas
     seguintes, `metadata.rag_results.rag_query` tende a ficar **vazio**, embora a busca ocorra;
   * o modelo/cota é escolhido uma vez por conexão (`create_log` usa a mesma cota).
5. **Falha após salvar a pergunta.** Se a I.A. falhar, a mensagem do usuário permanece salva sem resposta e
   conta no limite de 8 mensagens; uma nova tentativa no mesmo estado gera dois `user` consecutivos no
   histórico reconstruído.
6. **Ordem de comparação em `generate_chunks`.** `d.embeddings.all()` usa `ordering = ("-id",)`; para
   dispositivos com **mais de um chunk**, a comparação posicional com os chunks novos pode considerar
   "diferente" e recriar os embeddings (custo extra, sem erro de dados).
7. **Chunk vazio.** Se o primeiro texto de um dispositivo exceder 1536 palavras, o laço de divisão adiciona
   um `current_chunk` vazio antes, que seria persistido apenas com o prefixo do T.A.
8. **`total_tokens=0` por falha de API** impede a vetorização (a task filtra `total_tokens__gt=0`).
9. **FTS com AND** (`plainto_tsquery`): consultas longas reduzem a recuperação textual; a mitigação está
   no prompt (palavras-chave curtas e múltiplas tentativas).

### Manutenção

10. `print(self._chat.get_history())` em `chat_send_message` é depuração e deve usar `logger.debug`.
11. Código morto em `task_sync_embeddings_textoarticulado_function` (após `continue`) e em
    `generate_chunks` (`if False:`).
12. `make_context__old` e `make_context__20260225` não são mais usados.
13. `Embedding.vetor` (3072) é legado; `prepare_query` não é utilizado.
14. Docstrings de `Embedding` mencionam `text-embedding-3-large` (OpenAI); o modelo efetivo é
    `gemini-embedding-2` com 1536 dimensões.

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
