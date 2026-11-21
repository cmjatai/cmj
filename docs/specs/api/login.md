# API: login por usuário e senha

Status: implementado
Última verificação: 2026-11-21 (branch `v8-arquitetura-hibrida`, sobre o commit `a63428717`)
Código principal: `cmj/api/views.py`, `sapl/api/urls.py`, `cmj/urls.py`
Testes: `cmj/api/tests/test_login.py`

O login feito pela API segue o mesmo limite de tentativas da tela `/login/`, e a sessão por cookie
só é aberta ou encerrada com o token CSRF.

## Escopo

O limite de tentativas e a conferência do token CSRF nas duas rotas de login da API:
`/api/auth/session` (`AppSessionAuthView`) e `/api/auth/token` (`AppTokenAuthView`). O restante do
comportamento dessas rotas e da autenticação da API não tem spec.

## Regras

### Limite de tentativas

- API-AUTH-001 [implementado] `POST /api/auth/session` e `POST /api/auth/token` contam as tentativas
  por IP. Passado o limite de `RATE_LIMITER_RATE`, o mesmo da tela `/login/`, a resposta é 429 com
  `Retry-After`, e a credencial enviada não é avaliada. Evidência: `cmj/api/views.py:117`,
  `cmj/urls.py:144`.
- API-AUTH-002 [implementado] As duas rotas compartilham uma única contagem, a do grupo
  `cmj.api.login`. Evidência: `cmj/api/views.py:117`.
- API-AUTH-003 [implementado] Só `POST` entra na contagem. Consultar a sessão (`GET`, `OPTIONS`) e
  encerrá-la (`DELETE`) não contam. Evidência: `cmj/api/views.py:117`.
- API-AUTH-004 [implementado] Dentro do limite, credencial válida abre a sessão ou devolve o token,
  e credencial inválida responde 400 com `non_field_errors`. Evidência: `cmj/api/views.py:130`,
  `cmj/api/views.py:136`.
- API-AUTH-005 [observado] A contagem fica no cache `default`. Com `DummyCache`, que é o cache em
  `DEBUG`, nada é guardado e o limite não atua, aqui e na tela `/login/`. Evidência:
  `cmj/settings/project.py:160-167`, `cmj/settings/project.py:213-220`. Por leitura do código.

### Token CSRF

- API-AUTH-006 [implementado] `POST` e `DELETE` em `/api/auth/session` exigem o token CSRF, no
  cabeçalho `X-CSRFToken` ou no campo `csrfmiddlewaretoken`, também de quem ainda não está
  autenticado. Sem o token a resposta é 403, e a sessão não é aberta nem encerrada. Evidência:
  `cmj/api/views.py:135`.
- API-AUTH-007 [implementado] `GET /api/version` e `GET /api/auth/session` entregam o cookie
  `csrftoken`, de modo que o cliente tem o token antes de entrar. O v6 e o v2018 consultam
  `/api/version` ao abrir a página. Evidência: `cmj/api/views.py:57`, `cmj/api/views.py:170`.
- API-AUTH-008 [implementado] `POST /api/auth/token` não exige token CSRF: a resposta é um token de
  API, e nenhum cookie de sessão é criado. Evidência: `cmj/api/views.py:130`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, no recorte das duas rotas, em 2026-11-21.

## Dúvidas

Nenhuma.

## Fora do escopo

- O limite da tela `/login/`, que já existia.
- Limite por conta, além do limite por IP.
