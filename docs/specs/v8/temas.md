# V8: temas e modos

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `2ba9aef96`)
Código principal: `cmj/v8/services/s_global.py`, `_frontend/v8/src/css/app.css`,
`_frontend/v8/src/css/temas/`, `cmj/v8/views.py`
Testes: `cmj/v8/tests/test_temas.py`, `cmj/v8/tests/test_ds.py`,
`_frontend/v8/tests/css/temas.spec.js`, `_frontend/v8/tests/core/fonte.spec.js`,
`_frontend/v8/tests/core/shell.spec.js`, `_frontend/v8/tests/core/global.spec.js`

Tema é o design do v8: cores, fontes, arredondamentos, sombras e, se preciso, regras CSS próprias.
Modo é claro ou escuro. Todo tema tem os dois modos, e os dois são escolhas independentes.

O tema `oficial` é o CSS padrão do v8: a customização do que vem do Tailwind e do Reka UI. Os outros
temas partem dele e só alteram o que quiserem. A lista de temas é fixa no código. Cada navegador
pode escolher um tema da lista, guardado em cookie, e todas as páginas do v8 passam a abrir nele.

```text
_frontend/v8/src/css/
├─ app.css                 Tailwind, @source e um @import por tema, o oficial primeiro
└─ temas/
   ├─ oficial/             index.css, tokens.css e o CSS dos elementos, shell, componentes e overlays
   ├─ tema1/               index.css, tokens.css e, opcional, regras.css
   └─ ...
```

## Escopo

- Serviço: `cmj/v8/services/s_global.py` (registro de temas e de modos, preferências, cookie).
- CSS: `_frontend/v8/src/css/app.css` e as pastas de `_frontend/v8/src/css/temas/`.
- Pontos de entrada: `<html data-tema>` em toda página do v8 e as rotas de tema do design system
  (`/v8/ds/temas/`, `/v8/ds/temas/<nome>/` e `/v8/ds/temas/<nome>/usar/`), cujas páginas estão em
  `ds.md`.
- Legado tocado: nenhum. Nada fora de `cmj/v8`, `_templates/v8`, `_frontend/v8` e `docs/` muda.

Regras de outras specs que mudam com esta (D2):

| Spec | Regras | Mudança |
| --- | --- | --- |
| `arquitetura.md` | V8-ARQ-051 | Retirada: os tokens passam a ficar no `tokens.css` de cada tema (V8-TEMA-011) |
| `shell.md` | V8-SHELL-042 | Retirada: substituída pelas regras de cor de cada tema (V8-TEMA-012 e 013) |
| `shell.md` | V8-SHELL-020, 040, 041, 052 | Mesmo comportamento, com "modo" no lugar de "tema": cookie `v8_modo`, atributo `data-modo`, botão `data-v8-acao="modo"` |
| `templates.md` | V8-TPL-013, 016, 021, 041 | `<html>` passa a ter sempre `data-tema`; o botão do cabeçalho passa a ser o de modo |
| `arquitetura.md` | V8-ARQ-004, 023, 067 | Os cookies de preferência passam a ser `v8_tema`, `v8_modo` e `v8_sidebar`; o JSON global ganha `modo` |
| `overlays.md`, `shell.md`, `templates.md` | Evidências em CSS | O CSS do v8 passa para `css/temas/oficial/` |

## Regras

### Tema e modo

- V8-TEMA-001 [implementado] Tema é o design; modo é `claro` ou `escuro`. Todo tema define os dois
  modos. Trocar o tema não muda o modo, e trocar o modo não muda o tema. Evidência:
  `cmj/v8/services/s_global.py:130`, `_frontend/v8/src/core/shell.js:159`.
- V8-TEMA-002 [implementado] Os temas são um registro fixo em `s_global.TEMAS`, de nome para rótulo,
  com `oficial` como padrão. O nome tem só minúsculas, dígitos e hífen, começa por letra e não é o
  nome de um modo. Registro fora dessas regras impede o projeto de subir. Evidência:
  `cmj/v8/services/s_global.py:50`, `cmj/v8/services/s_global.py:68`.
- V8-TEMA-003 [implementado] Cada tema do registro tem a pasta `css/temas/<nome>/`, com `index.css`,
  e `app.css` importa os `index.css` na ordem do registro, com o `oficial` primeiro. Não há pasta
  nem import de tema fora do registro. Evidência: `_frontend/v8/src/css/app.css:11`.

### CSS

- V8-TEMA-010 [implementado] `css/temas/oficial/` reúne o CSS padrão do v8: tokens, elementos HTML,
  shell, componentes, overlays e componentes base. Só o oficial declara `@theme` e classes de
  componente. Evidência: `_frontend/v8/src/css/temas/oficial/index.css:5`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:131`.
- V8-TEMA-011 [implementado] Tokens (`--cor-*`, `--z-*`, `--duracao`, `--curva`, `--largura-*`,
  `--altura-*`, `--raio*`, `--deslocamento-*`, `--fonte-*`, `--sombra-*`) só são definidos no
  `tokens.css` de um tema. Camadas e movimento (`--z-*`, `--duracao`, `--curva`) só no oficial.
  Evidência: `_frontend/v8/src/css/temas/oficial/tokens.css:2`.
- V8-TEMA-012 [implementado] Cor literal só existe no `tokens.css` de um tema. Evidência:
  `_frontend/v8/src/css/temas/oficial/tokens.css:2`.
- V8-TEMA-013 [implementado] No oficial, toda `--cor-*` tem valor no modo claro, no escuro e no
  bloco que vale sem modo escolhido, que segue `prefers-color-scheme` sem JavaScript. Evidência:
  `_frontend/v8/src/css/temas/oficial/tokens.css:6`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:68`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:95`.
- V8-TEMA-014 [implementado] Um tema só redefine tokens que existem no oficial, sempre sob
  `:root[data-tema="<nome>"]`. Cor redefinida aparece nos três blocos do tema (claro, escuro e sem
  modo escolhido), para que a cor de um modo não vaze para o outro. Evidência:
  `_frontend/v8/src/css/temas/tema1/tokens.css:6`, `_frontend/v8/src/css/temas/tema2/tokens.css:6`.
- V8-TEMA-015 [implementado] As regras CSS próprias de um tema ficam em `regras.css`, na camada
  `temas`, que fica acima de `components` e abaixo de `utilities`. Todo seletor dele começa por
  `:root[data-tema="<nome>"]`. Tema não declara `@theme`, `@import`, `@font-face` nem `@layer` com
  outro nome. Evidência: `_frontend/v8/src/css/temas/tema3/regras.css:5`.
- V8-TEMA-016 [implementado] O `@theme inline` do oficial é o único e expõe ao Tailwind as cores
  semânticas, as fontes e os raios, por `var()`. Com isso as utilities seguem o tema e o modo em
  vigor. A paleta padrão do Tailwind continua fora. Evidência:
  `_frontend/v8/src/css/temas/oficial/tokens.css:131`.
- V8-TEMA-017 [implementado] `font-family` e `box-shadow` fora do `tokens.css` usam token, e
  `border-radius` usa token, `0` ou `50%`. Evidência:
  `_frontend/v8/src/css/temas/oficial/tokens.css:52`,
  `_frontend/v8/src/css/temas/oficial/tokens.css:62`,
  `_frontend/v8/src/css/temas/oficial/shell.css:12`.

### Aplicação

- V8-TEMA-020 [implementado] Toda página do v8 sai com `<html data-tema="<nome>">`, sempre com um
  nome do registro: o tema que a página de prévia fixa, senão o do cookie `v8_tema` se estiver no
  registro, senão `oficial`. Evidência: `cmj/v8/services/s_global.py:119`,
  `cmj/v8/templatetags/v8_tags.py:49`, `_templates/v8/base_v8.html:3`.
- V8-TEMA-021 [implementado] `#v8-global` informa `tema`, sempre um nome do registro, e `modo`, que
  é `claro`, `escuro` ou `null`. Evidência: `cmj/v8/services/s_global.py:290`,
  `_frontend/v8/src/stores/GlobalStore.js:25`.
- V8-TEMA-022 [implementado] A prévia de um tema não grava nada: abrir `/v8/ds/temas/<nome>/` não
  cria nem altera cookie. Evidência: `cmj/v8/views.py:424`.
- V8-TEMA-023 [implementado] "Usar este tema" é um `POST` que grava `v8_tema` e redireciona para a
  lista de temas, com mensagem. Dali em diante as páginas do v8 abrem nesse tema, naquele navegador.
  Funciona sem JavaScript. Evidência: `cmj/v8/views.py:486`, `_templates/v8/v8/ds/vitrine.html:4`.
- V8-TEMA-024 [implementado] `/v8/ds/temas/` lista os temas do registro, na ordem dele, cada um com
  rótulo, link para a prévia e o botão de usar, e marca o tema em vigor. Evidência:
  `cmj/v8/services/s_ds.py:108`, `_templates/v8/v8/ds/temas.html:6`.
- V8-TEMA-025 [implementado] Ao carregar a página e ao trocar o modo, `<meta name="theme-color">`
  recebe o valor de `--cor-barra-navegador` em vigor, que cada tema pode redefinir. Evidência:
  `_frontend/v8/src/core/shell.js:159`.

## Requisitos de segurança

- V8-TEMA-040 [implementado] Nome de tema só chega ao HTML, ao JSON e ao cookie depois de conferido
  no registro. Cookie com outro valor vale como `oficial`, e as rotas de prévia e de uso existem só
  para os nomes do registro: outro nome responde 404. Itens da varredura: 4 e 6. Evidência:
  `cmj/v8/urls.py:72`, `cmj/v8/services/s_global.py:119`.
- V8-TEMA-041 [implementado] Usar um tema exige superusuário, aceita só `POST` com CSRF e não grava
  nada além do cookie. Item da varredura: 1. Evidência: `cmj/v8/views.py:492`.
- V8-TEMA-042 [implementado] O redirecionamento depois de usar um tema é fixo: `next`, `Referer` e o
  corpo da requisição são ignorados. Item da varredura: 6. Evidência: `cmj/v8/views.py:497`.
- V8-TEMA-043 [implementado] O cookie `v8_tema` sai com `Path=/v8/`, `SameSite=Lax`, `HttpOnly`,
  `Secure` fora de DEBUG e um valor do registro. Item da varredura: 6. Evidência:
  `cmj/v8/services/s_global.py:146`.
- V8-TEMA-044 [implementado] O trecho do menu em `{% cache %}` não depende do tema, e o CSS de todos
  os temas é o mesmo arquivo estático. Item da varredura: 5. Evidência:
  `_templates/v8/v8/shell/menu.html:5`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-22, na revisão do código escrito.

## Dúvidas

- D1. Nomes de tema e de modo. Até aqui o código chamava o claro e o escuro de "tema" (cookie
  `v8_tema`, `<html data-theme>`). Recomendação: renomear para "modo" (`v8_modo`, `data-modo`) e
  deixar "tema" para o design (`v8_tema`, `data-tema`), porque o v8 só tem a demonstração e o custo
  é o menor possível agora. Quem tinha escolhido o escuro volta uma vez ao padrão do sistema.
  Alternativa: manter `v8_tema` e `data-theme` para o modo e dar outro nome ao design. Decisão
  (2026-11-22): renomear.
- D2. Como registrar as mudanças nas outras specs. Recomendação: V8-ARQ-051 e V8-SHELL-042
  recebem `[retirada]`, substituídas pelas regras V8-TEMA, porque o que elas exigiam (um arquivo
  único de tokens, dois temas) deixa de valer. As demais da tabela do Escopo mantêm o ID e têm texto
  e evidência atualizados, como na D9 de `templates.md`. Decisão: pendente; aplicada a recomendação.
- D3. Escolha do tema. Recomendação: lista fixa no código, escolha por navegador em cookie, e sem
  escolha vale o `oficial`. Alternativa: só a prévia, sem escolha. Decisão (2026-11-22): escolha
  por cookie, valendo para todo o v8 naquele navegador.
- D4. O que um tema pode mudar. Recomendação: só tokens. Alternativa: tokens e regras CSS próprias.
  Decisão (2026-11-22): tokens e regras CSS (V8-TEMA-015).
- D5. Onde ficam as pastas. O pedido fala em uma subpasta `oficial` na pasta `css` e em temas que a
  customizam. Recomendação: `css/temas/oficial/` ao lado de `css/temas/<nome>/`, espelhando a URL
  `/v8/ds/temas/<nome>/`. Alternativa: `css/oficial/` e `css/temas/<nome>/`. Decisão: pendente;
  aplicada a recomendação.
- D6. Três blocos de cor por tema ou `light-dark()`. Com `light-dark()` cada tema teria um bloco só,
  mas o piso de navegadores sobe para Safari 17.5, Chrome 123 e Firefox 120, e o JavaScript deixa
  de conseguir ler `--cor-barra-navegador` diretamente. Recomendação: três blocos, com teste de
  paridade. Decisão: pendente; aplicada a recomendação.
- D7. `data-tema` sempre emitido, inclusive com `oficial`. Recomendação: sempre, para o CSS e os
  testes terem um único caso. Alternativa: só quando o tema não é o oficial. Decisão: pendente;
  aplicada a recomendação.
- D8. Temas de exemplo. Os nomes `tema1`, `tema2` e `tema3` vieram do pedido; o conteúdo não.
  Recomendação: cada um exercita uma capacidade: `tema1` troca só cores, `tema2` troca cores,
  fontes e raios, e `tema3` tem também `regras.css`. Decisão: pendente; aplicada a recomendação.
- D9. Quem pode escolher o tema. Recomendação: por ora, só quem acessa o design system
  (superusuário, D1 de `ds.md`). Para abrir a escolha a todos, a lista sairia do design system e
  iria para o cabeçalho ou para uma página de preferências. Decisão: pendente; aplicada a
  recomendação.

## Fora do escopo

- Guardar o tema no perfil do usuário, no banco.
- Fontes web: os temas usam pilhas de fontes do sistema, sem `@font-face`.
- Carregar o CSS de cada tema separadamente: todos vão no mesmo arquivo.
- Rebuild de `dist/`.
