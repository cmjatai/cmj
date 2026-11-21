# V8: cliente HTTP

Status: implementado
Última verificação: 2026-11-21 (branch `v8-arquitetura-hibrida`, sobre o commit `32325c9a2`)
Código principal: `_frontend/v8/src/http/`, `cmj/v8/views.py`, `cmj/v8/services/s_respostas.py`
Testes: `_frontend/v8/tests/http/`, `cmj/v8/tests/test_http.py`, `_frontend/v8/tests/stores/auth.spec.js`,
`_frontend/v8/tests/overlays/formularios.spec.js`

Toda requisição do v8 passa por um cliente único, que cuida do CSRF, da sessão expirada e de
entregar os erros sempre no mesmo formato.

## Escopo

- Frontend: `src/http/client.js` (o cliente), `src/http/errors.js` (`HttpError` e a normalização) e
  `src/http/sessao.js` (fluxo de sessão expirada).
- Django: a resposta de erro de validação e a resposta 401 das views do v8.
- Legado alcançado: `/api/version` e `/api/auth/session` (`cmj/api/views.py:51-178`), e a tela
  `/login/` (`cmj/core/views_auth.py`).

## Regras

### Cliente

- V8-HTTP-001 [implementado] `client.js` expõe `get`, `post`, `put`, `patch` e `delete`. Nenhum
  outro arquivo de `_frontend/v8/src` chama `fetch`, `XMLHttpRequest` ou axios. Evidência:
  `_frontend/v8/src/http/client.js:3`.
- V8-HTTP-002 [implementado] O cliente envia os cookies da sessão só para a mesma origem. Corpo em
  objeto vai como JSON, `FormData` vai como está, e `params` vira query string. Evidência:
  `_frontend/v8/src/http/client.js:60`.
- V8-HTTP-003 [implementado] Em `POST`, `PUT`, `PATCH` e `DELETE`, o cliente envia `X-CSRFToken` com
  o valor do cookie `csrftoken` lido no momento da requisição. Evidência:
  `_frontend/v8/src/http/client.js:75`.
- V8-HTTP-004 [implementado] Toda página do v8 garante que o cookie `csrftoken` exista. Evidência:
  `cmj/v8/views.py:47`.
- V8-HTTP-005 [implementado] Toda requisição leva `X-Requested-With: XMLHttpRequest` e um `Accept`
  conforme o pedido: `application/json` ou, para fragmentos, `text/html`. Evidência:
  `_frontend/v8/src/http/client.js:72`.
- V8-HTTP-006 [implementado] Resposta JSON é devolvida já convertida, resposta HTML como texto, e
  204 como `null`. Evidência: `_frontend/v8/src/http/client.js:115`.
- V8-HTTP-007 [implementado] O cliente aceita um sinal de cancelamento. Requisição cancelada rejeita
  com código `cancelada` e não gera aviso ao usuário. Evidência:
  `_frontend/v8/src/http/sessao.js:121`.

### Formato de erro

- V8-HTTP-010 [implementado] Toda falha rejeita com `HttpError`, que tem `status`, `codigo`,
  `mensagem`, `campos` (nome do campo para lista de mensagens) e `gerais` (lista de mensagens).
  Evidência: `_frontend/v8/src/http/errors.js:1`.
- V8-HTTP-011 [implementado] `codigo` é um destes: `validacao` (400 e 422), `nao_autenticado`,
  `sem_permissao`, `nao_encontrado` (404), `conflito` (409), `servidor` (500 em diante), `rede` e
  `cancelada`. Evidência: `_frontend/v8/src/http/errors.js:1`.
- V8-HTTP-012 [implementado] O corpo de erro do DRF (`campo`, `non_field_errors`, `detail`) e o
  corpo de erro do v8 (`detail`, `errors`, `non_field_errors`) resultam no mesmo `HttpError`. Erro
  de campo aninhado vira chave com ponto, como `endereco.cep`. Evidência:
  `_frontend/v8/src/http/errors.js:1`.
- V8-HTTP-013 [implementado] Os endpoints do v8 respondem erro de validação com 400 e o corpo
  `{"detail", "errors", "non_field_errors"}`, montado por uma única função a partir dos erros do
  formulário Django. Evidência: `cmj/v8/services/s_respostas.py:18`.
- V8-HTTP-014 [implementado] O cliente não mostra aviso por conta própria. A exceção é o fluxo de
  sessão expirada. Quem chama decide entre toast, erro no formulário ou nada. Evidência:
  `_frontend/v8/src/http/client.js:5`.

### Sessão expirada

- V8-HTTP-020 [implementado] Sessão expirada é uma resposta 401, ou uma resposta 403 seguida de
  `/api/version` informando que não há usuário autenticado. Um 403 com usuário autenticado é
  `sem_permissao`. Evidência: `_frontend/v8/src/http/sessao.js:1`.
- V8-HTTP-021 [implementado] Se a página foi carregada com usuário autenticado, a sessão expirada
  abre o modal de reautenticação e a requisição fica pendente. Várias requisições nessa situação
  abrem um único modal. Evidência: `_frontend/v8/src/http/sessao.js:1`.
- V8-HTTP-022 [implementado] O modal oferece "Entrar em nova aba", que abre a tela `/login/`
  existente, e "Ir para o login", que sai da página. Ao voltar o foco para a página, o modal
  consulta `/api/version`. Evidência: `_frontend/v8/src/http/ModalSessao.vue:44`,
  `_frontend/v8/src/http/sessao.js:1`.
- V8-HTTP-023 [implementado] Confirmada a sessão do mesmo usuário, o modal fecha e cada requisição
  pendente é refeita uma única vez. Uma segunda falha de sessão na mesma requisição rejeita com
  `nao_autenticado`. Evidência: `_frontend/v8/src/http/sessao.js:1`,
  `_frontend/v8/src/stores/AuthStore.js:70`.
- V8-HTTP-024 [implementado] Dispensar o modal ou escolher "Ir para o login" rejeita as pendentes
  com `nao_autenticado` e leva à tela de login, com retorno para a página atual. Antes de sair, vale
  a guarda de alterações não salvas de `overlays.md`. Evidência:
  `_frontend/v8/src/http/sessao.js:1`.
- V8-HTTP-025 [implementado] Se a página foi carregada como anônimo, a sessão expirada não abre
  modal: a requisição rejeita com `nao_autenticado`. Evidência: `_frontend/v8/src/http/sessao.js:1`.
- V8-HTTP-026 [implementado] Endpoint ou fragmento do v8 que exige autenticação responde 401 em JSON
  a uma requisição do cliente, e redireciona ao login uma navegação comum. Evidência:
  `cmj/v8/views.py:93`.

### Código existente do v8

- V8-HTTP-030 [implementado] `Resources.Utils` passa a usar o cliente e mantém as assinaturas atuais
  e a resposta no formato `{ data }`. O pacote `axios` sai do v8. Evidência:
  `_frontend/v8/src/utils/resources/index.js:5`.

## Requisitos de segurança

- V8-HTTP-040 [implementado] O cliente recusa URL de outra origem. O token CSRF e os cookies nunca
  são enviados para fora da origem da página. Item da varredura: 6. Evidência:
  `_frontend/v8/src/http/client.js:26`.
- V8-HTTP-041 [implementado] O endereço de retorno ao login é montado só com o caminho e a query da
  página atual. Não vem de parâmetro, resposta nem atributo. Item da varredura: 6. Evidência:
  `_frontend/v8/src/core/navegacao.js:15`, `_frontend/v8/src/http/sessao.js:87`.
- V8-HTTP-042 [implementado] Se, após a reautenticação, o usuário for diferente do que carregou a
  página, a página é recarregada e nenhuma requisição pendente é refeita. Item da varredura: 1.
  Evidência: `_frontend/v8/src/http/sessao.js:67`.
- V8-HTTP-043 [implementado] O v8 não pede, não trafega e não guarda senha: a autenticação acontece
  só na tela `/login/` existente. Item da varredura: 5. Evidência:
  `_frontend/v8/src/http/ModalSessao.vue:45`, `_frontend/v8/src/utils/resources/index.js:9`.
- V8-HTTP-044 [implementado] Mensagem de erro vinda do servidor é mostrada como texto, nunca como
  HTML. Item da varredura: 4. Evidência: `_frontend/v8/src/overlays/ErrosGerais.vue:12`,
  `_frontend/v8/src/overlays/CampoForm.vue:17`.
- V8-HTTP-045 [implementado] O que o cliente registra no console sobre um erro não inclui o corpo da
  requisição. Item da varredura: 5. Evidência: `_frontend/v8/src/http/client.js:138`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-21. O login pela API tem spec própria, em
`docs/specs/api/login.md`.

## Dúvidas

- D1. O prompt pede um cliente `fetch` central, e o v8 herdou `Resources.Utils` sobre axios, usado
  por `SyncStore` e `AuthStore`. Recomendação: reescrever `Resources.Utils` sobre o cliente novo,
  mantendo as assinaturas, e remover o axios, para que haja um só caminho de requisição e o
  tratamento de sessão valha em tudo. Alternativa: manter o axios para `Resources.Utils` e usar o
  cliente novo só no código novo. Decisão (2026-11-21): um cliente só, e o axios sai do v8.
- D2. Como reautenticar sem perder o que está na tela. Recomendação: o modal abre a tela `/login/`
  existente em nova aba e retoma ao detectar a sessão. Aproveita o limite de tentativas e o login
  social dessa tela, e o v8 nunca manipula senha. Alternativas: formulário de usuário e senha no
  próprio modal, enviando a `/api/auth/session`, ou sempre redirecionar ao
  login, perdendo o estado da tela. Decisão (2026-11-21): modal que abre `/login/` em nova aba.

## Fora do escopo

- Cache de respostas, repetição automática em erro de rede e fila offline.
- Upload com progresso.
