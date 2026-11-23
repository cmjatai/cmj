# V8: componentes base

Status: implementado
Última verificação: 2026-11-22 (branch `refact_v8`, sobre o commit `2ba9aef96`)
Código principal: `_frontend/v8/src/componentes/`, `_frontend/v8/src/css/temas/oficial/primitivos.css`,
`_frontend/v8/src/css/temas/oficial/campos.css`, `_frontend/v8/src/css/temas/oficial/estrutura.css`,
`_frontend/v8/src/css/temas/oficial/datas.css`, `_frontend/v8/src/css/temas/oficial/cor.css`
Testes: `_frontend/v8/tests/componentes/componentes.spec.js`,
`_frontend/v8/tests/componentes/campos.spec.js`,
`_frontend/v8/tests/componentes/estrutura.spec.js`, `_frontend/v8/tests/componentes/datas.spec.js`,
`_frontend/v8/tests/componentes/cor.spec.js`, `_frontend/v8/tests/componentes/textos.spec.js`

Componentes Vue de uso geral, construídos sobre as primitivas do Reka UI e vestidos pelo tema em
vigor. São a base das telas do v8 e aparecem na vitrine do design system (`ds.md`). Cobrem todas
as primitivas do Reka UI que têm visual próprio; as que duplicam o que o v8 já tem e as que não têm
visual ficam fora (Fora do escopo).

### Base

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

### Campos

| Componente | Primitivas do Reka UI | Uso |
| --- | --- | --- |
| `Rotulo` | Label | Rótulo de campo |
| `Alternador` | Toggle | Botão que fica pressionado |
| `GrupoAlternadores` | ToggleGroup | Um ou vários valores entre botões lado a lado |
| `Deslizante` | Slider | Número, ou intervalo, numa faixa |
| `CampoNumero` | NumberField | Número com botões de mais e menos, formatado em pt-BR |
| `CampoCodigo` | PinInput | Código com uma casa por caractere |
| `CampoEtiquetas` | TagsInput | Lista de textos digitados como etiquetas |
| `TextoEditavel` | Editable | Texto que vira campo no lugar |
| `Avaliacao` | Rating | Nota em estrelas |
| `SelecaoBusca` | Combobox | Escolha numa lista filtrada pelo texto digitado |
| `Autocompletar` | Autocomplete | Texto livre com sugestões |
| `ListaOpcoes` | Listbox | Lista de opções sempre visível |
| `GrupoEtiquetas` | TagGroup | Etiquetas existentes, selecionáveis e removíveis |

### Navegação e estrutura

| Componente | Primitivas do Reka UI | Uso |
| --- | --- | --- |
| `Recolhivel` | Collapsible | Um trecho que abre e fecha |
| `BarraFerramentas` | Toolbar | Botões, links e alternadores agrupados |
| `BarraMenus` | Menubar | Menus de aplicativo na horizontal |
| `MenuContexto` | ContextMenu | Menu do botão direito |
| `MenuNavegacao` | NavigationMenu | Links de navegação com painéis |
| `CartaoFlutuante` | HoverCard | Prévia ao passar o mouse num link |
| `Paginacao` | Pagination | Páginas de uma lista |
| `Etapas` | Stepper | Passos de um processo |
| `Arvore` | Tree | Itens hierárquicos que abrem e fecham |
| `Divisor` | Splitter | Painéis com divisória arrastável |
| `AreaRolagem` | ScrollArea | Rolagem com barra própria |
| `Separador` | Separator | Linha entre conteúdos |
| `Avatar` | Avatar | Imagem de pessoa, com iniciais na falta dela |
| `Progresso` | Progress | Barra de progresso |
| `Proporcao` | AspectRatio | Caixa com proporção fixa |

### Datas e horas

| Componente | Primitivas do Reka UI | Uso |
| --- | --- | --- |
| `Calendario` | Calendar | Escolha de um dia num calendário |
| `CalendarioPeriodo` | RangeCalendar | Escolha de um período num calendário |
| `CampoData` | DateField | Data digitada por partes |
| `CampoPeriodo` | DateRangeField | Período digitado por partes |
| `SeletorData` | DatePicker | Data digitada ou escolhida num calendário |
| `SeletorPeriodo` | DateRangePicker | Período digitado ou escolhido num calendário |
| `CampoHora` | TimeField | Hora digitada por partes |
| `CampoIntervaloHoras` | TimeRangeField | Intervalo de horas |
| `SeletorMes` | MonthPicker | Escolha de um mês |
| `SeletorMeses` | MonthRangePicker | Escolha de um intervalo de meses |
| `SeletorAno` | YearPicker | Escolha de um ano |
| `SeletorAnos` | YearRangePicker | Escolha de um intervalo de anos |

### Cor

| Componente | Primitivas do Reka UI | Uso |
| --- | --- | --- |
| `AreaCor` | ColorArea | Cor escolhida num plano de dois canais |
| `CampoCor` | ColorField | Cor digitada em hexadecimal |
| `DeslizanteCor` | ColorSlider | Um canal da cor numa faixa |
| `AmostraCor` | ColorSwatch | Amostra de uma cor |
| `PaletaCores` | ColorSwatchPicker | Escolha entre cores prontas |

## Escopo

- Frontend: a pasta `componentes` de `_frontend/v8/src/` e o CSS dos componentes no tema oficial.
- Pontos de entrada: nenhum novo. Os componentes são usados por ilhas, zonas e overlays, e a
  vitrine os mostra numa seção por grupo, cada uma com a sua ilha.
- Dependência declarada: `@internationalized/date`, que o Reka UI já instalava, passa a constar do
  `package.json` do v8, porque os componentes de data convertem os valores com ela (D5).
- Legado tocado: nenhum.

## Regras

- V8-CMP-001 [implementado] Os componentes base ficam em `src/componentes/`, um por arquivo, com os
  nomes das tabelas acima, e cada um usa as primitivas do Reka UI correspondentes. Evidência:
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

### Grupos

- V8-CMP-010 [implementado] Os componentes de campo da tabela "Campos" ficam em `src/componentes/`,
  cada um sobre a primitiva indicada. `GrupoAlternadores`, `Deslizante`, `CampoNumero`,
  `CampoCodigo`, `CampoEtiquetas`, `TextoEditavel`, `Avaliacao`, `SelecaoBusca`, `Autocompletar` e
  `ListaOpcoes`, com `name` e dentro de um `<form>`, participam do envio nativo. O `Alternador`
  participa como uma caixa de marcação, com um campo oculto próprio: vai o `value` só quando está
  pressionado (D6). Evidência: `_frontend/v8/src/componentes/Deslizante.vue:8`,
  `_frontend/v8/src/componentes/SelecaoBusca.vue:6`, `_frontend/v8/src/componentes/Alternador.vue:11`.
- V8-CMP-011 [implementado] `CampoNumero` formata e lê o número no idioma pt-BR, e no formulário vai o
  número sem formatação. Evidência: `_frontend/v8/src/componentes/CampoNumero.vue:10`.
- V8-CMP-020 [implementado] Os componentes da tabela "Navegação e estrutura" ficam em
  `src/componentes/`, cada um sobre a primitiva indicada. O conteúdo flutuante de `BarraMenus`,
  `MenuContexto` e `CartaoFlutuante` vai para o `body`, na camada `--z-popover`, e o painel do
  `MenuNavegacao` também usa essa camada. Evidência: `_frontend/v8/src/componentes/MenuContexto.vue:9`, `_frontend/v8/src/css/temas/oficial/estrutura.css:112`.
- V8-CMP-030 [implementado] Os componentes da tabela "Datas e horas" ficam em `src/componentes/`, cada
  um sobre a primitiva indicada, no idioma pt-BR. O v-model é texto ISO: `AAAA-MM-DD` para dia,
  `HH:MM` para hora, `AAAA-MM` para mês e `AAAA` para ano, e `{ inicio, fim }` para período e
  intervalo. Texto que não é uma data válida vale como vazio. A conversão fica num só módulo,
  `src/componentes/datas.js`. Evidência: `_frontend/v8/src/componentes/datas.js:34`, `_frontend/v8/src/componentes/Calendario.vue:2`.
- V8-CMP-031 [implementado] Mês e ano escolhidos saem sem o dia nem o mês de hoje: `SeletorMes` devolve
  só ano e mês, e `SeletorAno`, só o ano. Com `name`, todo componente de data põe o valor no
  formulário num campo oculto próprio, no mesmo texto ISO do v-model; período e intervalo vão em
  `<name>_inicio` e `<name>_fim`, vazios quando não preenchidos.
  Evidência: `_frontend/v8/src/componentes/datas.js:44`, `_frontend/v8/src/componentes/datas.js:53`, `_frontend/v8/src/componentes/CampoPeriodo.vue:61`.
- V8-CMP-035 [implementado] Os componentes da tabela "Cor" ficam em `src/componentes/`, cada um sobre
  a primitiva indicada, com o v-model em texto hexadecimal. O código não tem cor literal: as cores
  de amostra da vitrine são lidas dos tokens do tema em vigor. Evidência: `_frontend/v8/src/componentes/PaletaCores.vue:2`, `_frontend/v8/src/modules/ds/ilhas/DsCor.vue:71`.
- V8-CMP-008 [implementado] Os textos que o Reka UI traz em inglês (rótulos de botões de mais e menos,
  de páginas, de remover, de mostrar opções, de passos e de calendário) saem em português nos
  componentes. Evidência: `_frontend/v8/src/componentes/datas.js:13`, `_frontend/v8/src/componentes/Etapas.vue:39`, `_frontend/v8/src/componentes/Paginacao.vue:17`.

## Requisitos de segurança

- V8-CMP-040 [implementado] Os componentes não renderizam HTML recebido por prop: rótulos e textos
  são interpolados como texto. Item da varredura: 4. Evidência:
  `_frontend/v8/src/componentes/Abas.vue:18`.

## Riscos de segurança

Nenhum risco encontrado nos itens 1 a 7, em 2026-11-22, na revisão do código escrito.

## Dúvidas

- D1. Nomes dos componentes. Recomendação: em português, como o resto do v8 (`Abas`, `Sanfona`,
  `Dica`, `MenuSuspenso`, `Selecao`, `CaixaMarcacao`, `GrupoOpcoes`, `Chave`), mantendo `Popover`,
  que não tem nome corrente em português. Alternativa: os nomes do Reka UI em inglês. Decisão
  (2026-11-22): em português.
- D2. Quais primitivas entram agora. Decisão (2026-11-22): o lote essencial desta spec; as demais
  primitivas do Reka UI ficam como prioridade do próximo plano (Fora do escopo).
- D3. Uma spec própria para os componentes. Recomendação: sim, separada de `ds.md`, porque a
  biblioteca vai crescer e não é assunto da página da vitrine. Decisão: pendente; aplicada a
  recomendação.

- D4. O que entra em "todo o Reka UI". Decisão (2026-11-22): só as primitivas com visual novo. Ficam
  fora as que duplicam o que o v8 já tem e os utilitários sem visual (Fora do escopo).
- D5. Declarar `@internationalized/date` no `package.json`. Os componentes de data precisam dela
  para ir e voltar do texto ISO, e o Reka UI não a reexporta. Recomendação: declarar a mesma versão
  já instalada (3.12.4), mudando só o `package.json` e o lock. Alternativa: componentes de data com
  v-model nos objetos de data do Reka, sem conversão, o que leva esse tipo para quem usa o
  componente. Decisão: pendente; aplicada a recomendação.
- D6. `Alternador` no formulário. O Toggle do Reka UI 2.11 gera um campo oculto que nunca fica
  marcado, então o valor não iria no envio. Recomendação: um campo oculto próprio no componente,
  que envia o `value` só quando pressionado, como uma caixa de marcação. Alternativa: deixar o
  `Alternador` fora do formulário. Decisão (2026-11-22): campo oculto próprio.
- D7. Nomes dos componentes novos. Recomendação: em português, como os do primeiro lote (tabelas
  acima), mantendo `Avatar`. Decisão (2026-11-22): em português, junto com a D1.
- D8. Formato do v-model das datas. Recomendação: texto ISO (V8-CMP-030), o mesmo dos formulários
  do Django e da API, e `{ inicio, fim }` para períodos. Alternativa: os objetos de data do Reka.
  Decisão: pendente; aplicada a recomendação.

## Fora do escopo

- Primitivas do Reka UI que duplicam o v8: Dialog, AlertDialog e Drawer (a pilha de overlays do v8
  já usa o Dialog), Toast (os toasts do v8) e Form e Field (o `CampoForm` e os erros do Django).
- Utilitários sem visual: ConfigProvider, FocusScope, VisuallyHidden, Primitive, Presence,
  Teleport, Viewport, Collection, DismissableLayer, RovingFocus e Popper.
- Conferir no jsdom a navegação por setas das primitivas: fica para a conferência no navegador.
- Componentes de regra de negócio do projeto.
- Substituir as classes `v8-*` usadas nas páginas Django por componentes Vue.
