# V2018: infraestrutura de testes

Status: implementado, com duas regras acordadas sem teste (V2018-TST-007 e 008), que descrevem escopo
Última verificação: 2026-11-21 (commit `dc27ae6d6`)
Código principal: `_frontend/v2018/vitest.config.mjs`, `_frontend/v2018/tests/setup.js`, `_frontend/v2018/tests/apoio.js`, `_frontend/v2018/package.json`, `.github/workflows/ci.yml`
Testes: `_frontend/v2018/tests/`, `cmj/core/test_specs_check.py`

O v2018 continua em uso a médio e longo prazo e não tinha teste automatizado. Esta spec define a
infraestrutura para rodá-los e os testes iniciais, que cobrem só a estrutura descrita em
[`estrutura.md`](./estrutura.md).

## Escopo

- Não há serviço nem ponto de entrada no backend: a capacidade é de desenvolvimento. O que seria a
  classe de serviço é a configuração dos testes (`vitest.config.mjs` e `tests/setup.js`).
- Arquivos novos: `_frontend/v2018/vitest.config.mjs` e `_frontend/v2018/tests/`.
- Arquivos existentes alterados: `_frontend/v2018/package.json` (scripts `test` e `test:watch`, seis
  `devDependencies`), `.github/workflows/ci.yml` (job `frontend-v2018`),
  `cmj/core/services/s_specs_check.py` (lê os títulos dos testes do v2018) e a documentação.
- Nenhum arquivo de `_frontend/v2018/src` foi alterado.

Os testes de estrutura apontam para as regras de `estrutura.md`. As regras desta spec são
conferidas por `tests/sanidade.spec.js`, por `tests/estrutura/infra.spec.js` e, no caso do
`specs_check`, por `cmj/core/test_specs_check.py`.

## Regras

- V2018-TST-001 [implementado] `npm test`, em `_frontend/v2018`, roda todos os testes uma vez e termina
  com código diferente de zero se algum falhar. Não precisa de dev server, backend, banco nem build.
  Evidência: `_frontend/v2018/package.json:11`.
- V2018-TST-002 [implementado] Os testes usam Vitest com jsdom e `@vue/test-utils` 1, a mesma
  ferramenta e a mesma convenção do v8. O build e o dev server continuam com o Vue CLI. Evidência:
  `_frontend/v2018/vitest.config.mjs:44`.
- V2018-TST-003 [implementado] A configuração dos testes é separada e não executa o `vue.config.js`.
  Evidência: `_frontend/v2018/vitest.config.mjs:7-8`.
- V2018-TST-004 [implementado] O ambiente de teste repete o que o webpack fornece ao código de `src/`:
  o alias `@`, os globais `$`, `jQuery` e `_`, o import de componente sem `.vue`, o
  `<template lang="html">` e a compilação de template em tempo de execução. Evidência:
  `_frontend/v2018/vitest.config.mjs:15`, `_frontend/v2018/vitest.config.mjs:29-41`,
  `_frontend/v2018/tests/setup.js:14`.
- V2018-TST-005 [implementado] Os testes ficam em `_frontend/v2018/tests/**/*.spec.js`, fora de `src/`,
  em `estrutura/` (regras conferidas lendo arquivos), `app/` (peças da entrada `app`), `entradas/`
  (subida das outras entradas) e `apps/` (comportamento dos módulos de `src/__apps`, numa subpasta
  por módulo). O apoio comum fica em `tests/apoio.js`. Evidência:
  `_frontend/v2018/vitest.config.mjs:45`.
- V2018-TST-006 [implementado] O teste que cobre uma regra de spec abre o título com o ID dela, e o
  `specs_check` lê os títulos dos testes do v2018 como lê os do v8. Evidência:
  `cmj/core/services/s_specs_check.py:47`.
- V2018-TST-007 [acordado] Os testes iniciais cobrem a estrutura: entradas, bundles pedidos
  pelos templates, subida das entradas, store, mixin global, `Resources.Utils` e rotas. Teste de
  regra de negócio de um módulo entra em `apps/` quando a correção do módulo pede, ligado à regra
  da spec do módulo. Evidência: `_frontend/v2018/tests/sanidade.spec.js:7`.
- V2018-TST-008 [acordado] Nenhum arquivo de `src/` é alterado para acomodar teste. O que o teste
  precisa e o jsdom não tem entra em `tests/setup.js`. Evidência:
  `_frontend/v2018/tests/setup.js:36`.
- V2018-TST-009 [implementado] O CI roda `npm ci` e `npm test` do v2018 em cada push e PR para o
  `master`. Não roda lint, que corrige arquivos, nem build. Evidência:
  `.github/workflows/ci.yml:40-55`.

## Requisitos de segurança

Varredura sobre os pontos de entrada da capacidade, que são o comando `npm test` e o job do CI.
Itens 1 a 5 não se aplicam: não há view, endpoint, arquivo servido nem execução no servidor.

- V2018-TST-020 [implementado] Nenhum teste faz requisição de rede: `tests/setup.js` faz falhar
  `XMLHttpRequest`, `fetch` e `WebSocket`, e quem precisa de HTTP usa o axios falso. Item da
  varredura: 6 e 7. Evidência: `_frontend/v2018/tests/setup.js:48-59`.
- V2018-TST-021 [implementado] Os testes não leem `.env` nem credenciais. O `vue.config.js`, que carrega
  o `.env` do backend, é lido como texto e nunca executado. Item da varredura: 6. Evidência:
  `_frontend/v2018/tests/estrutura/entradas.spec.js:2`.
- V2018-TST-022 [implementado] O job do CI não usa segredo, não publica artefato e não acessa banco nem
  produção. Item da varredura: 6. Evidência: `.github/workflows/ci.yml:40-55`.
- V2018-TST-023 [implementado] As bibliotecas de teste ficam em `devDependencies` e nenhum arquivo de
  `src/` as importa: elas não entram no bundle de produção. Item da varredura: 6. Evidência:
  `_frontend/v2018/package.json:60`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7 para o código novo, em 2026-11-21. Os riscos do legado
alcançado estão em [`estrutura.md`](./estrutura.md).

## Dúvidas

- D1. Vitest ou Jest. Decisão (2026-11-21): manter o Vitest. É o que o v8 usa, o `specs_check` já lê
  os títulos, e o Jest que serve ao Vue 2 está parado numa versão antiga. Custo aceito: os testes
  transformam o código com o Vite, e não com o webpack e o Babel do build, então um erro que só o
  webpack acusa não aparece nos testes. Resolvida.
- D2. `src/__globals` e a entrada `compilacao` não são importáveis nos testes: os plugins do jQuery
  UI só se registram pelo carregador AMD do webpack. O teste de subida da entrada `app` troca
  `src/__globals` por um módulo vazio. Decisão (2026-11-21): aceitar a lacuna. Se essa camada
  precisar de cobertura, o caminho é teste em navegador, com spec própria. Resolvida.
- D3. Conferência do build depois das mudanças de dependências. O dev server compilou as cinco
  entradas e o rebuild dos três frontends foi feito pelo responsável em 2026-11-21 (commit
  `636568f45`), sem erro. Pendência do responsável: conferir as telas do portal no navegador, em
  especial o editor TinyMCE e as mensagens. Decisão: pendente.
- D4. Sem `package-lock.json` versionado, o CI instalava versões que mudavam sem commit. Decisão
  (2026-11-21), em D7 de `estrutura.md`: o lock é versionado e o CI usa `npm ci`. Resolvida.
- D5. Versão do Node no CI. Decisão (2026-11-21): fixar `24.22.3`, a mesma dos containers de
  desenvolvimento e do rebuild, nos jobs do v8 e do v2018. Quando o Dockerfile mudar, o CI muda
  junto. Resolvida.
- D6. `npm run lint` (`vue-cli-service lint`) alcança também `tests/`. Decisão (2026-11-21): manter.
  Os testes seguem o padrão do ESLint do projeto. Resolvida.
- D7. Confirmação das regras. Decisão (2026-11-21): o responsável confirmou todas. As que têm
  comportamento verificável ganharam teste e passaram a `[implementado]`; V2018-TST-007 e 008, que
  descrevem escopo, ficam `[acordado]`. Resolvida.

## Fora do escopo

- Testes de regra de negócio dos módulos (`src/modules`, `src/__apps/loa`, `src/__construct`).
- Testes em navegador e de ponta a ponta.
- Cobertura de código e limite mínimo de cobertura.
- Mudança no build, no lint ou nas dependências de produção.
