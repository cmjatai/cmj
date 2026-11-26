# V8: troca de portal

Status: implementado
Última verificação: 2026-11-25 (branch `v8-troca-portal`, sobre o commit `b9d20d308`)
Código principal: `cmj/v8/services/s_portal.py`, `cmj/v8/middleware.py`, `cmj/v8/urls_raiz.py`,
`cmj/v8/views.py`, `_templates/v8/v8/partials/portal/`
Testes: `cmj/v8/tests/test_portal.py`

O v8 vai substituir o v2018 com as mesmas URLs do portal. Esta capacidade monta só a troca: um
superusuário liga o v8 no próprio navegador por um cookie assinado e, com ele, o Django resolve as
rotas com outro conjunto, em que as páginas já migradas para o v8 vêm antes do portal inteiro. A
única página migrada é a inicial: com o cookie, `/` abre a página inicial do v8.

## Escopo

- Serviço: `cmj/v8/services/s_portal.py`. Middleware: `cmj/v8/middleware.py`, que só lê o cookie e
  escolhe o conjunto de rotas. Conjunto de rotas da raiz: `cmj/v8/urls_raiz.py`.
- Pontos de entrada: `POST /v8/portal/ativar/`, `POST /v8/portal/desativar/` e o próprio middleware,
  que vale para toda requisição.
- Botões: `_templates/v8/v8/partials/portal/ativar_v2018.html`, incluído pela página inicial do
  v2018, e o formulário de voltar, escrito no block `header_actions` de `_shell.html` (as parciais
  do shell são só as de V8-TPL-041).
- Legado tocado: `cmj/settings/middleware.py` (uma linha) e `_templates/v2018/path/pagina_inicial.html`
  (um `include`). As duas mudanças estão no Escopo de `arquitetura.md`.

## Regras

### Escolha das rotas

- V8-PORTAL-001 [implementado] Sem cookie `v8_portal` válido, a requisição usa o `ROOT_URLCONF`
  (`cmj.urls`) e nada muda. O `PortalV8Middleware` vem logo depois do `AuthenticationMiddleware`.
  Evidência: `cmj/v8/middleware.py:14`, `cmj/settings/middleware.py:12`.
- V8-PORTAL-002 [implementado] Com cookie válido, a requisição usa `cmj.v8.urls_raiz`: `/` responde
  com a página inicial do v8, no layout `landing`, e qualquer outro caminho resolve para a mesma view
  e o mesmo nome de rota que teria sem o cookie, porque o resto é o `cmj.urls` inteiro. O `reverse()`
  devolve os mesmos caminhos nos dois modos. Evidência: `cmj/v8/middleware.py:16`,
  `cmj/v8/urls_raiz.py:15`, `cmj/v8/urls_raiz.py:16`.

### Cookie

- V8-PORTAL-003 [implementado] O cookie `v8_portal` tem `Path=/`, `HttpOnly`, `SameSite=Lax`,
  `Secure` fora do DEBUG e validade de 12 horas. O valor é o pk de quem o emitiu, assinado com data
  (`TimestampSigner`, `salt` próprio). A validade é conferida na leitura: cookie adulterado, sem
  assinatura, de outro `salt` ou vencido conta como ausente. O cookie continua valendo depois do
  logout (D1). Evidência: `cmj/v8/services/s_portal.py:33`, `cmj/v8/services/s_portal.py:57`.

### Ligar e desligar

- V8-PORTAL-004 [implementado] `POST /v8/portal/ativar/` grava o cookie e só atende superusuário:
  anônimo vai para o login e usuário comum recebe o 403 do v8, os dois sem cookie. Depois volta para
  o destino de V8-PORTAL-006. Evidência: `cmj/v8/views.py:505`, `cmj/v8/services/s_portal.py:26`.
- V8-PORTAL-005 [implementado] `POST /v8/portal/desativar/` apaga o cookie para qualquer pessoa,
  inclusive anônima, e volta para o destino de V8-PORTAL-006. Evidência: `cmj/v8/views.py:523`,
  `cmj/v8/services/s_portal.py:52`.
- V8-PORTAL-006 [implementado] O destino é o campo `next` só quando ele é caminho do mesmo host:
  começa por `/`, não por `//`, não tem `\` e passa em `url_has_allowed_host_and_scheme`. Senão, o
  destino é `/`. Evidência: `cmj/v8/services/s_portal.py:68`.

### Botões

- V8-PORTAL-007 [implementado] O botão "Conferir o novo portal" aparece na página inicial do v2018
  só para superusuário. O `include` fica fora dos fragmentos `{% cache %}` da página, de modo que
  nenhum cache guarda o botão para outro usuário. Evidência:
  `_templates/v2018/path/pagina_inicial.html:10`, `cmj/v8/templatetags/v8_tags.py:196`.
- V8-PORTAL-008 [implementado] O botão "Voltar ao portal antigo" aparece no cabeçalho das páginas do
  v8 com shell quando a requisição tem o cookie válido, inclusive para anônimo, e volta para o mesmo
  caminho. Sem o cookie, não aparece. Evidência: `_templates/v8/v8/layouts/_shell.html:14`,
  `cmj/v8/templatetags/v8_tags.py:202`.

### Rotas da raiz

- V8-PORTAL-009 [implementado] `cmj.v8.urls_raiz` usa o mesmo `handler403` de `cmj.urls`, porque o
  Django lê o handler do conjunto de rotas da requisição: o 429 do rate limit continua igual.
  Evidência: `cmj/v8/urls_raiz.py:11`.

## Requisitos de segurança

- V8-PORTAL-010 [implementado] O cookie só escolhe o conjunto de rotas: não dá permissão. As views do
  v8 continuam conferindo o acesso pelo `AcessoV8Mixin`, a resposta do v8 continua com
  `Cache-Control: private`, e o serviço não recebe a requisição. Itens da varredura: 1 e 5.
  Evidência: `cmj/v8/middleware.py:15`, `cmj/v8/views.py:512`.
- V8-PORTAL-011 [implementado] Ligar e desligar aceitam só `POST` com CSRF. Um cookie forjado não
  vale, porque a assinatura depende da `SECRET_KEY`. Item da varredura: 6. Evidência:
  `cmj/v8/views.py:513`, `cmj/v8/views.py:526`, `cmj/v8/services/s_portal.py:22`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-25, na revisão do código escrito.

## Dúvidas

- D1. O cookie vale depois do logout? Opções: continuar valendo até expirar, para conferir o v8 como
  anônimo, ou exigir superusuário logado a cada requisição. Recomendação: continuar valendo, com
  validade de 12 horas. Decisão: continua valendo (usuário, 2026-11-25).

## Fora do escopo

- Migrar qualquer página além da inicial, e o `crud8`.
- Preferências do shell do v8 (tema, modo, sidebar): os cookies têm `Path=/v8/` (V8-ARQ-004) e não
  chegam a `/`, que abre no tema padrão.
- Links do menu e da marca do v8, que continuam apontando para `/v8/...`.
- `Vary: Cookie` nas respostas do legado. Um cache na frente do Django pode entregar o `/` do v2018 a
  quem tem o cookie, o que só atrasa a troca.
- Service worker da raiz: continua o do v2018. O v8 registra só o de escopo `/v8/`.
