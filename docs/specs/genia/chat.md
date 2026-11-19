# Genia: chat RAG

Status: implementado
Última verificação: 2026-11-19 (branch `refactor/genia`, sobre o commit `d6741e498`)
Código principal: `cmj/utils/genia/chat.py`, `cmj/utils/genia/genia_system_instruction_v3.py`,
`cmj/search/chat_manager.py`, `cmj/search/consumers.py`
Testes: `cmj/utils/genia/test_genia.py`, `cmj/search/test_chat_manager.py`

## Escopo

`IAChatService`: o que o chat RAG acrescenta à classe-base, ou seja, system instruction, formato de
resposta, cota própria e limites de uso por usuário. O fluxo do chat (WebSocket, histórico,
recuperação) está em `docs/rag/04-chat-websocket-e-llm.md`.

## Regras

### Configuração

- GENIA-CHAT-001 [implementado] Só o chat usa `rag_system_instruction`, e responde em `text/plain`.
  Evidência: `cmj/utils/genia/chat.py:23-24`.
- GENIA-CHAT-004 [observado] Com `DEBUG=True`, a system instruction inclui a regra da palavra-chave
  `RAGRAG`, que libera conversa técnica sobre o RAG. Evidência:
  `cmj/utils/genia/genia_system_instruction_v3.py:3-6`.

### Cota do modelo

- GENIA-CHAT-002 [implementado] Cada mensagem consome a cota autorizada para a chave `IAGenaiBase`,
  escolhendo a de menor `quota_diaria` com margem. O modelo da cota é o usado na conversa e fica em
  `ia_model_name`, que o `ChatManager` grava no metadata da resposta. Evidência:
  `cmj/utils/genia/chat.py:21`, `cmj/utils/genia/chat.py:32-45`, `cmj/search/chat_manager.py:96-107`.
- GENIA-CHAT-003 [implementado] Sem cota disponível, nenhuma conversa é aberta na API e
  `IAQuotaUnavailableError` sobe até o `ChatConsumer`, que devolve a mensagem de erro ao usuário.
  Evidência: `cmj/utils/genia/chat.py:35`, `cmj/search/consumers.py:153`.
- GENIA-CHAT-005 [implementado] Cada mensagem abre um `Chat` novo na API com o histórico recebido e
  registra um consumo de peso 1 depois da resposta. Evidência: `cmj/utils/genia/chat.py:36-43`.
  Teste: `cmj/search/test_chat_manager.py` (`test_chat_e_criado_a_cada_mensagem_e_cota_registrada`).

### Limites de uso por usuário

Os valores ficam em `IAChatService` (`cmj/utils/genia/chat.py:28-30`). Quem aplica é o
`ChatManager`, que os reexpõe com os mesmos nomes (`cmj/search/chat_manager.py:14-16`), porque a
verificação depende de `ChatSession` e `ChatMessage`.

- GENIA-CHAT-006 [observado] Um usuário cria no máximo 2 conversas por dia. Evidência:
  `cmj/search/chat_manager.py:116-126`.
- GENIA-CHAT-007 [observado] Uma conversa aceita no máximo 8 mensagens, somando as do usuário e as do
  modelo. Evidência: `cmj/search/chat_manager.py:134-140`.
- GENIA-CHAT-008 [observado] A mensagem do usuário tem no máximo 200 caracteres. Evidência:
  `cmj/search/consumers.py:118-125`.
- GENIA-CHAT-009 [observado] Superusuário não tem limite de conversas nem de mensagens, e pode enviar
  até 10000 caracteres. Evidência: `cmj/search/chat_manager.py:123`,
  `cmj/search/chat_manager.py:135`, `cmj/search/consumers.py:119-120`.
- GENIA-CHAT-010 [observado] Quando um superusuário conecta, a lista de modelos da API é sincronizada
  com `IAQuota` (GENIA-BASE-012). Evidência: `cmj/search/consumers.py:51-55`.

## Mudança de comportamento na refatoração

Antes, a system instruction só era enviada quando havia `tools`. Agora vai em toda mensagem do chat.
O `ChatManager` sempre envia a tool `buscar_na_base_dados`, então o fluxo atual não mudou.

## Dúvidas

- D1. O chat consome a chave de cota `IAGenaiBase`, que no admin aparece como "IA Genai Base". O nome
  vem de quando o chat usava a classe-base direto. Trocar para uma chave própria (por exemplo
  `IAChatService`) exige migration de `cmj.core` alterando os `choices` e copiando a autorização nas
  `IAQuota` existentes. Em produção, com blue/green, a migration precisa manter a chave antiga até a
  versão anterior sair do ar. Fazer a troca?
- D2. O limite de 2 conversas por dia compara `created_at__date` com a data local, e o de 8
  mensagens conta as respostas do modelo, o que dá 4 perguntas por conversa. É esse o limite
  pretendido?
- D3. Uma mensagem pode gerar até 10 chamadas ao modelo por function calling e conta 1 na cota (ver
  D2 de [conexao-e-cotas.md](./conexao-e-cotas.md)).

## Fora do escopo

Recuperação híbrida, histórico e protocolo WebSocket (`docs/rag/`). Geração do embedding da consulta
([embeddings.md](./embeddings.md)).
