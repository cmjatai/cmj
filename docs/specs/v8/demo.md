# V8: demonstração

Status: implementado
Última verificação: 2026-11-21 (branch `v8-arquitetura-hibrida`, sobre o commit `32325c9a2`)
Código principal: `cmj/v8/services/s_demo.py`, `cmj/v8/views.py`, `_templates/v8/v8/demo/`,
`_frontend/v8/src/modules/demo/`
Testes: `cmj/v8/tests/test_demo.py`, `_frontend/v8/tests/demo/`, `_frontend/v8/tests/overlays/url.spec.js`

Duas telas que exercitam tudo o que as outras specs do v8 definem, com dados fictícios: uma página
Django com ilhas e uma zona SPA. Servem de referência de uso e de roteiro de verificação manual.

## Escopo

- Serviço: `cmj/v8/services/s_demo.py`, com os clientes fictícios e as validações.
- Pontos de entrada:

| Rota | Tipo |
| --- | --- |
| `/v8/demo/clientes/` | Página Django com ilhas |
| `/v8/demo/clientes/arquivar/` | `POST` da ação em massa, que redireciona para a lista |
| `/v8/demo/clientes/<id>/` | Página de detalhe, destino dos links sem JavaScript |
| `/v8/_frag/demo/cliente/<id>/historico/` | Fragmento HTML |
| `/v8/demo/spa/` e subcaminhos | Zona SPA `demo-spa` |
| `/v8/demo/api/clientes/` | JSON: lista (`GET`) e criação (`POST`) |
| `/v8/demo/api/clientes/<id>/` | JSON: detalhe (`GET`) e edição (`PUT`) |
| `/v8/demo/api/negado/` | JSON: responde sempre 403, para a regra V8-DEMO-025 |

- Legado tocado: nenhum.

## Regras

### Dados

- V8-DEMO-001 [implementado] Os clientes são uma lista fixa, gerada em memória por `s_demo.py`, com
  nomes fictícios e e-mails no domínio `exemplo.invalid`. Não há CPF, telefone, endereço nem dado de
  pessoa real. Evidência: `cmj/v8/services/s_demo.py:63`.
- V8-DEMO-002 [implementado] Nada é gravado: criar, editar e arquivar validam a entrada e respondem
  como se tivessem gravado, e a lista continua a mesma. As telas avisam que é uma demonstração.
  Evidência: `_frontend/v8/src/modules/demo/api.js:2`.
- V8-DEMO-003 [implementado] A validação de cliente é um formulário Django em `s_demo.py`: nome
  obrigatório com ao menos três letras, e-mail válido e ainda não usado por outro cliente (erros de
  campo), e situação "inativo" só com motivo preenchido (erro geral). Evidência:
  `cmj/v8/services/s_demo.py:89`.

### Página Django com ilhas

- V8-DEMO-010 [implementado] `/v8/demo/clientes/` renderiza no servidor a lista paginada e filtrada
  por `q`, `situacao` e `cidade`, no layout `admin`. Com o JavaScript desligado, filtrar, paginar,
  abrir o detalhe e arquivar funcionam. Evidência: `cmj/v8/views.py:254`,
  `_templates/v8/v8/demo/clientes.html:1`.
- V8-DEMO-011 [implementado] A tabela é a ilha `demo-clientes-tabela`: o HTML do servidor é o
  conteúdo de espera, e o componente acrescenta seleção de linhas, "selecionar todos" e a contagem
  dos selecionados. Evidência: `_frontend/v8/src/modules/demo/ilhas/ClientesTabela.vue:74`.
- V8-DEMO-012 [implementado] Os filtros são o formulário `GET` da página. Em tela larga ficam num
  drawer esquerdo `docked`, e em tela estreita abrem como drawer `overlay`, pelo gatilho
  `data-drawer="el:#demo-filtros"`. Evidência: `_templates/v8/v8/demo/clientes.html:7`,
  `_frontend/v8/src/core/triggers.js:185`.
- V8-DEMO-013 [implementado] O link de cada cliente abre o detalhe num drawer direito e põe
  `?painel=cliente:<id>` na URL. O botão voltar fecha o drawer, e abrir a URL copiada reabre o mesmo
  detalhe. Evidência: `_frontend/v8/src/modules/demo/paineis/PainelCliente.vue:37`.
- V8-DEMO-014 [implementado] No detalhe, "Histórico" abre um segundo drawer, empilhado, com o
  fragmento `frag:demo/cliente/<id>/historico`. Evidência:
  `_frontend/v8/src/modules/demo/paineis/PainelCliente.vue:40`.
- V8-DEMO-015 [implementado] "Arquivar selecionados" é um formulário `POST` com `data-confirm`.
  Confirmada, a ação responde com redirecionamento e uma mensagem do Django, que aparece como toast
  na página seguinte. Evidência: `cmj/v8/views.py:285`, `_templates/v8/v8/demo/clientes.html:38`.

### Zona SPA

- V8-DEMO-020 [implementado] `/v8/demo/spa/` mostra a lista de clientes, carregada da API da demo,
  no layout `spa`. Evidência: `_frontend/v8/src/modules/demo/spa/ClientesLista.vue:127`,
  `_frontend/v8/src/modules/demo/spa/DemoSpaLayout.vue:11`.
- V8-DEMO-021 [implementado] `/v8/demo/spa/clientes/<id>` é rota aninhada e mostra o detalhe num
  drawer direito sobre a lista. `/v8/demo/spa/clientes/<id>/pedidos/<pedido>` empilha um segundo
  drawer. Abrir qualquer uma dessas URLs diretamente chega ao mesmo estado. Evidência:
  `_frontend/v8/src/modules/demo/spa/ClienteDetalhe.vue:41`,
  `_frontend/v8/src/modules/demo/spa/ClientesLista.vue:128`.
- V8-DEMO-022 [implementado] "Editar" abre um modal `form`. Um erro de validação da API aparece
  junto ao campo ou no topo do modal, e fechar com alteração pendente pede confirmação. Ao salvar, o
  modal fecha e um toast de sucesso é disparado pelo Vue. Evidência:
  `_frontend/v8/src/modules/demo/modais/ClienteForm.vue:114`,
  `_frontend/v8/src/modules/demo/spa/ClienteDetalhe.vue:45`.
- V8-DEMO-023 [implementado] "Novo cliente" abre um modal `wizard` de três passos, que envia à API
  ao concluir. Evidência: `_frontend/v8/src/modules/demo/spa/ClientesLista.vue:130`,
  `_frontend/v8/src/modules/demo/wizard/PassoIdentificacao.vue:39`.
- V8-DEMO-024 [implementado] "Ampliar" abre um modal `fullscreen` com o resumo do cliente.
  Evidência: `_frontend/v8/src/modules/demo/modais/ClienteResumo.vue:34`,
  `_frontend/v8/src/modules/demo/spa/ClienteDetalhe.vue:46`.
- V8-DEMO-025 [implementado] Um botão da zona dispara uma requisição que responde 403, para mostrar
  o tratamento de `sem_permissao`. Evidência: `_frontend/v8/src/modules/demo/api.js:34`,
  `_frontend/v8/src/modules/demo/spa/ClientesLista.vue:131`.

## Requisitos de segurança

- V8-DEMO-030 [implementado] Todas as rotas da demonstração exigem superusuário, em qualquer
  ambiente. Anônimo é redirecionado ao login nas páginas e recebe 401 na API e nos fragmentos.
  Autenticado que não é superusuário recebe 403. Itens da varredura: 1 e 7. Evidência:
  `cmj/v8/views.py:255`.
- V8-DEMO-031 [implementado] As ações que simulam escrita aceitam só `POST` ou `PUT`, com CSRF. Item
  da varredura: 1. Evidência: `cmj/v8/views.py:289`, `cmj/v8/views.py:360`.
- V8-DEMO-032 [implementado] `id` inexistente responde 404 na página, na API e no fragmento. Os
  filtros aceitam só os campos previstos, e o tamanho da página tem limite máximo. Itens da
  varredura: 1 e 7. Evidência: `cmj/v8/views.py:247`, `cmj/v8/services/s_demo.py:18`.
- V8-DEMO-033 [implementado] Nenhuma rota da demonstração lê ou grava model, arquivo, cache
  compartilhado, fila ou índice. Itens da varredura: 3 e 5. Evidência:
  `cmj/v8/services/s_demo.py:85`.
- V8-DEMO-034 [implementado] As respostas da API da demo contêm só os campos fictícios do cliente.
  Item da varredura: 2. Evidência: `cmj/v8/services/s_demo.py:156`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-21. A demonstração não alcança código legado.

## Dúvidas

- D1. Quem acessa a demonstração. Recomendação: só superusuário, em qualquer ambiente, o que
  permite conferir a demo em produção sem expor rotas a anônimos. Alternativas: só com `DEBUG`
  ligado (404 em produção), ou qualquer usuário autenticado. Decisão (2026-11-21): só superusuário.

## Fora do escopo

- Persistir os dados da demonstração.
- Demonstrar popover, tooltip e os demais primitivos do Reka UI.
