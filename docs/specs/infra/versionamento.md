# Infra: versionamento de produção

Status: implementado
Última verificação: 2026-11-23 (commit `288399c0c`)
Código principal: `cmj/core/services/s_versao.py`, `cmj/settings/project.py`, `docker/Dockerfile`,
`.github/workflows/ci.yml`, `_frontend/versao.mjs`
Testes: `cmj/core/test_versao.py`, `_frontend/v8/tests/core/versao.spec.js`

O backend tem a versão `vAAAA.MM.N`, calculada do histórico do git, e cada frontend tem a sua,
`<frontend>.AAAA.MM.N`, incrementada a cada build. A versão do backend vira tag no GitHub; a de cada
frontend vai para o `package.json` e para dentro do service worker, o que força o navegador a trocar
o service worker a cada build.

## Escopo

Serviço `cmj/core/services/s_versao.py` (só biblioteca padrão: roda no CI e no servidor sem as
dependências do projeto). Pontos de entrada: `PORTALCMJ_VERSION` em `cmj/settings/project.py`, o
`docker/Dockerfile` e o compose de produção, o job de tag no `.github/workflows/ci.yml`, o script
`_frontend/versao.mjs` chamado pelo `prebuild` dos três frontends e os service workers do v6, do v8
e do v2018. O `deploy.sh` do servidor fica fora do repositório e passa a exportar a versão antes do
build da imagem (passo do usuário).

## Regras

- INFRA-VER-001 [implementado] A versão do backend para um commit é `vAAAA.MM.N`: `AAAA.MM` é o mês da
  data do committer desse commit no fuso `America/Sao_Paulo`, e `N` é a posição dele entre os
  commits da linha principal (first-parent) desse mês, contando a partir de 1. O mesmo commit
  sempre tem a mesma versão. Evidência: `cmj/core/services/s_versao.py:36-57`.
- INFRA-VER-002 [implementado] Commits que entram no master por merge, fora da linha principal, não
  contam no `N`. Evidência: `cmj/core/services/s_versao.py:45`.
- INFRA-VER-003 [implementado] Em clone raso a versão não é calculada: o serviço termina com erro em vez
  de devolver um `N` menor. Evidência: `cmj/core/services/s_versao.py:37-40`.
- INFRA-VER-004 [implementado] `PORTALCMJ_VERSION` vem da variável de ambiente de mesmo nome; sem ela,
  é calculada do git do diretório do projeto; sem git, vale `master`. Evidência: `cmj/settings/project.py:86-93`.
- INFRA-VER-005 [implementado] A imagem de produção recebe a versão pelo argumento de build
  `PORTALCMJ_VERSION`, repassado pelo compose de produção e pelo da produção simulada; sem ele, vale
  `master`. Evidência: `docker/Dockerfile:63-64`, `docker/docker-compose.yaml:58`,
  `docker/docker-compose.yaml:88`, `docker/docker-compose-dev-mode-prod.yaml:59`,
  `docker/prodsim/up.sh:28-33`.
- INFRA-VER-006 [implementado] A cada push no master o CI cria e envia a tag com a versão do último
  commit do push. Tag que já existe no mesmo commit não é recriada nem é erro; tag que existe em
  outro commit é erro (histórico reescrito). Evidência: `cmj/core/services/s_versao.py:60-81`, `.github/workflows/ci.yml:32`.
- INFRA-VER-007 [implementado] A cada `npm run build`, o `prebuild` de cada frontend grava a versão
  `<frontend>.AAAA.MM.N` no `package.json` e no `package-lock.json`: `N` soma 1 quando a versão
  anterior é do mesmo frontend e do mês atual (fuso `America/Sao_Paulo`), e volta a 1 nos outros
  casos. Evidência: `_frontend/versao.mjs:19-28`, `_frontend/versao.mjs:32-53`,
  `_frontend/v6/package.json:12`, `_frontend/v8/package.json:12`, `_frontend/v2018/package.json:9`.
- INFRA-VER-008 [implementado] O service worker de cada frontend carrega a versão do `package.json` em
  `self.PORTALCMJ_VERSAO`: cada build muda o arquivo e o navegador instala o service worker novo.
  Evidência: `_frontend/v6/vite.config.js:16`, `_frontend/v6/vite.config.js:38`,
  `_frontend/v6/src/service-worker.js:7`, `_frontend/v8/vite.config.js:16`,
  `_frontend/v8/vite.config.js:38`, `_frontend/v8/src/service-worker.js:7`,
  `_frontend/v2018/vue.config.js:204`, `_frontend/v2018/src/service-worker.js:10`.
- INFRA-VER-009 [implementado] O service worker do v2018 ativa assim que é instalado e assume as
  páginas abertas (`skipWaiting` e `clients.claim`), como o do v6 e o do v8. Evidência: `_frontend/v2018/src/service-worker.js:13-19`.

## Requisitos de segurança

- INFRA-VER-020 [implementado] O serviço chama o `git` com lista de argumentos, sem shell, e nenhum
  argumento vem de requisição: só `rev`, `repo` e o remoto, dados por quem roda o script. Item da
  varredura: 4. Evidência: `cmj/core/services/s_versao.py:23-33`.
- INFRA-VER-021 [implementado] Só o job de tag do CI tem `contents: write`; os demais jobs continuam
  sem permissão de escrita, e o job de tag não roda em pull request. Item da varredura: 6.
  Evidência: `.github/workflows/ci.yml:12-23`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7 (2026-11-23). A versão já era pública (schema da API e
`s_global` do v8, com o valor `master`) e continua sendo; ela não revela mais que o número de
commits do mês, que o repositório público já mostra.

## Dúvidas

- D1. Formato e contador do backend. Decisão (usuário, 2026-11-23): `vAAAA.MM.N`, `N` volta a 1
  em cada mês.
- D2. Quando criar a tag e quem cria. Decisão (usuário, 2026-11-23): a cada push no master, pelo
  GitHub Actions. O deploy roda no servidor, fora do alcance do CI, e a imagem não vai para o
  Docker Hub.
- D3. Atualização do service worker do v2018. Decisão (usuário, 2026-11-23): ativar na hora, como
  v6 e v8. O deploy já apaga os chunks antigos do `dist`, então esperar não protegia nada.

## Fora do escopo

O `deploy.sh` do servidor (fora do repositório) e o rebuild dos frontends, que ficam com o usuário.
