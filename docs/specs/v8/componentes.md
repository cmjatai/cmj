# V8: componentes base

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `485a3a988`)
Código principal: `_frontend/v8/src/componentes/`, `_frontend/v8/src/css/temas/oficial/primitivos.css`
Testes: `_frontend/v8/tests/componentes/componentes.spec.js`

Componentes Vue de uso geral, construídos sobre as primitivas do Reka UI e vestidos pelo tema em
vigor. São a base das telas do v8 e aparecem na vitrine do design system (`ds.md`). Este primeiro
lote cobre as primitivas mais usadas em formulários e em navegação dentro da página.

| Componente | Primitivas do Reka UI | Uso |
| --- | --- | --- |
| `Abas` | Tabs | Painéis alternados na mesma área |
| `Sanfona` | Accordion | Seções que abrem e fecham |
| `Dica` | Tooltip | Texto curto ao passar o mouse ou focar |
| `Popover` | Popover | Painel flutuante ancorado num gatilho |
| `MenuSuspenso` | DropdownMenu | Lista de ações aberta por um botão |
| `Selecao` | Select | Escolha de um valor numa lista |
| `CaixaMarcacao` | Checkbox | Marcar ou desmarcar, com estado indeterminado |
| `GrupoOpcoes` | RadioGroup | Uma opção entre várias |
| `Chave` | Switch | Liga e desliga |

## Escopo

- Frontend: a pasta `componentes` de `_frontend/v8/src/` e o CSS dos componentes no tema oficial.
- Pontos de entrada: nenhum novo. Os componentes são usados por ilhas, zonas e overlays, e a
  vitrine os mostra pela ilha `ds-componentes`.
- Legado tocado: nenhum.

## Regras

- V8-CMP-001 [implementado] Os componentes base ficam em `src/componentes/`, um por arquivo, com os
  nomes da tabela acima, e cada um usa as primitivas do Reka UI correspondentes. Evidência:
  `_frontend/v8/src/componentes/Abas.vue:43`, `_frontend/v8/src/componentes/Selecao.vue:85`.
- V8-CMP-002 [implementado] Cada componente é um invólucro fino: recebe os dados por props e devolve
  o valor por `v-model`, sem regra de negócio e sem requisição ao servidor. Evidência:
  `_frontend/v8/src/componentes/Abas.vue:56`, `_frontend/v8/src/componentes/Chave.vue:44`.
- V8-CMP-003 [implementado] O visual vem de classes `v8-*` do tema oficial, e os estados são lidos
  dos atributos que o Reka UI põe nos elementos (`data-state`, `data-disabled`, `data-highlighted`,
  `data-placeholder`), sem estado visual próprio em JavaScript. Evidência:
  `_frontend/v8/src/css/temas/oficial/primitivos.css:7`,
  `_frontend/v8/src/css/temas/oficial/primitivos.css:285`.
- V8-CMP-004 [implementado] O conteúdo flutuante de `Dica`, `Popover`, `MenuSuspenso` e `Selecao`
  vai para o `body` e usa a camada `--z-popover`, que fica acima de drawers, modals e toasts. Aberto
  dentro de um modal, ESC fecha só o flutuante. Evidência:
  `_frontend/v8/src/css/temas/oficial/primitivos.css:110`,
  `_frontend/v8/src/componentes/Popover.vue:6`.
- V8-CMP-005 [implementado] Os papéis ARIA e o teclado das primitivas são preservados: abas com
  `tablist` e `tab`, menu com `menu` e `menuitem`, seleção com `combobox`, e caixa de marcação,
  opção e chave com `checkbox`, `radio` e `switch`. Os componentes não interceptam tecla nem mudam
  `tabindex`, para valer o teclado do Reka UI. Evidência: `_frontend/v8/src/componentes/Abas.vue:7`.
- V8-CMP-006 [implementado] `CaixaMarcacao`, `GrupoOpcoes`, `Chave` e `Selecao`, com `name` e dentro
  de um `<form>`, participam do envio nativo do formulário. Evidência:
  `_frontend/v8/src/componentes/Selecao.vue:4`, `_frontend/v8/src/componentes/Chave.vue:7`.
- V8-CMP-007 [implementado] Os componentes não usam cor, raio, sombra, duração nem camada literais:
  tudo vem dos tokens, e por isso seguem o tema e o modo em vigor. Evidência:
  `_frontend/v8/src/css/temas/oficial/primitivos.css:105`.

## Requisitos de segurança

- V8-CMP-040 [implementado] Os componentes não renderizam HTML recebido por prop: rótulos e textos
  são interpolados como texto. Item da varredura: 4. Evidência:
  `_frontend/v8/src/componentes/Abas.vue:18`.

## Riscos de segurança

A varredura sobre o código entra no fechamento da implementação.

## Dúvidas

- D1. Nomes dos componentes. Recomendação: em português, como o resto do v8 (`Abas`, `Sanfona`,
  `Dica`, `MenuSuspenso`, `Selecao`, `CaixaMarcacao`, `GrupoOpcoes`, `Chave`), mantendo `Popover`,
  que não tem nome corrente em português. Alternativa: os nomes do Reka UI em inglês. Decisão:
  pendente; aplicada a recomendação.
- D2. Quais primitivas entram agora. Decisão (2026-11-22): o lote essencial desta spec; as demais
  primitivas do Reka UI ficam como prioridade do próximo plano (Fora do escopo).
- D3. Uma spec própria para os componentes. Recomendação: sim, separada de `ds.md`, porque a
  biblioteca vai crescer e não é assunto da página da vitrine. Decisão: pendente; aplicada a
  recomendação.

## Fora do escopo

- Prioridade do próximo plano: as demais primitivas do Reka UI (Combobox, Calendar, DatePicker,
  DateField, NumberField, PinInput, TagsInput, Slider, Toggle, ToggleGroup, Toolbar, Menubar,
  ContextMenu, NavigationMenu, HoverCard, Collapsible, Progress, ScrollArea, Splitter, Stepper,
  Pagination, Listbox, Tree, Avatar, Separator, Label, Editable, Rating, os de cor e de data em
  intervalo).
- Componentes de regra de negócio do projeto.
- Substituir as classes `v8-*` usadas nas páginas Django por componentes Vue.
