# V8: design system

Status: em implementação: as regras `[implementado]` têm teste; as `[desejado]` são das próximas
etapas
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `485a3a988`)
Código principal: `cmj/v8/services/s_ds.py`, `cmj/v8/views.py`, `cmj/v8/urls.py`,
`_templates/v8/v8/ds/`, `_templates/v8/v8/partials/ds/`
Testes: `cmj/v8/tests/test_ds.py`, `cmj/v8/tests/test_shell.py`

O design system do v8 é o lugar onde se vê como está o padrão visual: cada elemento HTML, cada
classe `v8-*`, os overlays, os ícones, os tokens e, depois, os componentes base do projeto, todos no
tema e no modo em vigor. Não é documentação: é um cenário, com amostras e rótulos curtos.

| Rota | Conteúdo |
| --- | --- |
| `/v8/ds/` | A vitrine, no tema em vigor |
| `/v8/ds/temas/` | A lista dos temas (`temas.md`) |
| `/v8/ds/temas/<nome>/` | A vitrine no tema `<nome>`, sem mudar a escolha do navegador |
| `/v8/ds/temas/<nome>/usar/` | `POST` que escolhe o tema `<nome>` para o navegador |

## Escopo

- Serviço: `s_ds.py` em `cmj/v8/services/`, com o registro das seções e os dados de amostra.
- Pontos de entrada: as quatro rotas acima, em `cmj/v8/views.py` e `cmj/v8/urls.py`, e as ilhas do
  design system no frontend.
- CSS: o estilo dos elementos HTML sem classe, no tema oficial.
- Legado tocado: nenhum.

## Regras

### Vitrine

- V8-DS-001 [implementado] `/v8/ds/` é uma página Django no layout `app_sidebar`, no tema e no modo em
  vigor. Evidência: `cmj/v8/views.py:423`, `_templates/v8/v8/ds/vitrine.html:1`.
- V8-DS-002 [implementado] As seções vêm de um registro em `s_ds.py`, com identificador, rótulo e
  parcial. Cada seção é uma parcial de `v8/partials/ds/`, com âncora `ds-<identificador>`, e o topo
  da página tem o índice das seções. Evidência: `cmj/v8/services/s_ds.py:33`, `_templates/v8/v8/ds/vitrine.html:15`.
- V8-DS-003 [desejado] A vitrine é um cenário: amostras com rótulos curtos (o nome da classe, do
  elemento ou do token), sem texto explicativo. Evidência: a criar.
- V8-DS-004 [desejado] Os dados de amostra são fixos e fictícios, declarados em `s_ds.py`.
  Evidência: a criar.
- V8-DS-005 [desejado] Toda `--cor-*` do tema oficial tem amostra, com o nome do token, e os
  tokens de fonte, raio e sombra também. Evidência: a criar.
- V8-DS-006 [desejado] Os elementos HTML aparecem sem classe, agrupados em títulos, texto, listas,
  tabela, formulário (todos os tipos de `input`, `select`, `textarea`, `fieldset`, `progress`,
  `meter`, estados desabilitado, só leitura e inválido) e interativos (`details`).
  Evidência: a criar.
- V8-DS-007 [desejado] Toda classe de `componentes.css` do oficial aparece na vitrine.
  Evidência: a criar.
- V8-DS-008 [desejado] Todo símbolo do sprite de ícones aparece, com o nome. Evidência: a criar.
- V8-DS-009 [desejado] Os drawers aparecem pelos gatilhos em HTML, nos dois lados, nos três
  tamanhos e nos três modos, com uma confirmação por `data-confirm`. Modals e toasts aparecem pela
  ilha `ds-overlays`. Evidência: a criar.
- V8-DS-010 [desejado] Sem JavaScript, as seções em HTML continuam completas, e as seções que
  dependem de ilha mostram um aviso no lugar. Evidência: a criar.
- V8-DS-011 [desejado] Elementos HTML sem classe recebem o estilo do tema só dentro do conteúdo da
  página e do corpo dos overlays. O cabeçalho, o menu e a moldura dos overlays não são afetados.
  Evidência: a criar.
- V8-DS-012 [implementado] O menu tem o grupo "Design system", com "Vitrine" e "Temas", visível só
  para quem acessa o design system. Evidência: `cmj/v8/services/s_menu.py:79`.
- V8-DS-013 [implementado] A prévia `/v8/ds/temas/<nome>/` é a mesma vitrine, no tema `<nome>`, com uma
  faixa no topo que traz o nome do tema, o botão "Usar este tema" e o link para a lista.
  Evidência: `cmj/v8/views.py:453`, `_templates/v8/v8/ds/vitrine.html:4`.
- V8-DS-014 [desejado] Os componentes base de `componentes.md` aparecem na seção "Componentes
  base", pela ilha `ds-componentes`. Evidência: a criar.

## Requisitos de segurança

- V8-DS-040 [implementado] Todas as rotas do design system exigem superusuário. Anônimo é levado ao
  login, e autenticado que não é superusuário recebe 403. Itens da varredura: 1 e 7.
  Evidência: `cmj/v8/views.py:430`, `cmj/v8/views.py:460`, `cmj/v8/views.py:485`.
- V8-DS-041 [implementado] A vitrine e a lista de temas aceitam só `GET` e `HEAD`. Item da varredura:
  1. Evidência: `cmj/v8/views.py:486`.
- V8-DS-042 [implementado] Nada da requisição é renderizado na vitrine, e a parcial de cada seção sai
  só do registro. Item da varredura: 4. Evidência: `_templates/v8/v8/ds/vitrine.html:18`.
- V8-DS-043 [implementado] Nenhuma rota do design system lê ou grava model, arquivo, cache
  compartilhado, fila ou índice. Itens da varredura: 3 e 5. Evidência: `cmj/v8/services/s_ds.py:1`.
- V8-DS-044 [desejado] As ilhas do design system não fazem requisição ao servidor. Item da
  varredura: 2. Evidência: a criar.

## Riscos de segurança

A varredura sobre o código entra no fechamento da implementação.

## Dúvidas

- D1. Quem acessa o design system. Recomendação: só superusuário, como a demonstração, porque a
  vitrine ainda é ferramenta de quem desenvolve. Alternativas: qualquer usuário autenticado, ou
  público. Decisão: pendente; aplicada a recomendação.
- D2. Onde vale o estilo dos elementos HTML sem classe. O Tailwind zera o estilo de todos eles.
  Recomendação: só dentro do conteúdo da página e do corpo dos overlays (V8-DS-011), e só em
  elemento sem `class`, para não mudar o shell nem os componentes. Alternativas: em toda a página,
  ou só dentro de uma classe opcional como `v8-prosa`. Decisão: pendente; aplicada a recomendação.
- D3. Uma página só ou uma página por seção. Recomendação: uma página com índice de âncoras, que
  permite ver tudo de uma vez e comparar temas rolando a mesma tela. Alternativa: uma página por
  seção, quando a vitrine crescer. Decisão: pendente; aplicada a recomendação.

## Fora do escopo

- Texto explicativo, exemplos de código e guia de uso: ficam em `docs/frontend/v8.md`.
- Componentes de regra de negócio do projeto: entram na vitrine quando forem criados.
- Comparar temas lado a lado na mesma tela.
