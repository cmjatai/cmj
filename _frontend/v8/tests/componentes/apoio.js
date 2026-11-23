// Apoio aos testes dos componentes base (docs/specs/v8/componentes.md).
import fs from 'fs'
import path from 'path'
import { mount } from '@vue/test-utils'

export const RAIZ = path.resolve(__dirname, '../..')
export const PASTA = path.join(RAIZ, 'src/componentes')
export const OFICIAL = path.join(RAIZ, 'src/css/temas/oficial')

// Cada componente base e o prefixo das partes do Reka UI que ele usa (ou a lista deles).
export const PRIMITIVAS = {
  // Base
  Abas: 'Tabs',
  Sanfona: 'Accordion',
  Dica: 'Tooltip',
  Popover: 'Popover',
  MenuSuspenso: 'DropdownMenu',
  Selecao: 'Select',
  CaixaMarcacao: 'Checkbox',
  GrupoOpcoes: 'RadioGroup',
  Chave: 'Switch',
  // Campos
  Rotulo: 'Label',
  Alternador: 'Toggle',
  GrupoAlternadores: 'ToggleGroup',
  Deslizante: 'Slider',
  CampoNumero: 'NumberField',
  CampoCodigo: 'PinInput',
  CampoEtiquetas: 'TagsInput',
  TextoEditavel: 'Editable',
  Avaliacao: 'Rating',
  SelecaoBusca: 'Combobox',
  Autocompletar: 'Autocomplete',
  ListaOpcoes: 'Listbox',
  GrupoEtiquetas: 'TagGroup',
  // Navegação e estrutura
  Recolhivel: 'Collapsible',
  BarraFerramentas: 'Toolbar',
  BarraMenus: 'Menubar',
  MenuContexto: 'ContextMenu',
  MenuNavegacao: 'NavigationMenu',
  CartaoFlutuante: 'HoverCard',
  Paginacao: 'Pagination',
  Etapas: 'Stepper',
  Arvore: 'Tree',
  Divisor: 'Splitter',
  AreaRolagem: 'ScrollArea',
  Separador: 'Separator',
  Avatar: 'Avatar',
  Progresso: 'Progress',
  Proporcao: 'AspectRatio',
  // Datas e horas
  Calendario: 'Calendar',
  CalendarioPeriodo: 'RangeCalendar',
  CampoData: 'DateField',
  CampoPeriodo: 'DateRangeField',
  SeletorData: 'DatePicker',
  SeletorPeriodo: 'DateRangePicker',
  CampoHora: 'TimeField',
  CampoIntervaloHoras: 'TimeRangeField',
  SeletorMes: 'MonthPicker',
  SeletorMeses: 'MonthRangePicker',
  SeletorAno: 'YearPicker',
  SeletorAnos: 'YearRangePicker',
  // Cor
  AreaCor: 'ColorArea',
  CampoCor: ['ColorField', 'ColorSwatch'],
  DeslizanteCor: 'ColorSlider',
  AmostraCor: 'ColorSwatch',
  PaletaCores: 'ColorSwatchPicker'
}

// Componentes que só exibem: não têm valor a devolver por v-model nem evento.
export const SO_EXIBICAO = ['Dica', 'Rotulo', 'Divisor', 'AreaRolagem', 'Separador', 'Avatar', 'Proporcao', 'AmostraCor']

// Os arquivos CSS do oficial onde ficam as classes dos componentes.
export const CSS_DOS_COMPONENTES = ['primitivos.css', 'campos.css', 'estrutura.css', 'datas.css', 'cor.css']

export const ler = arquivo => fs.readFileSync(arquivo, 'utf8')
export const fonte = nome => ler(path.join(PASTA, `${nome}.vue`))

const montados = []

export function montar(componente, opcoes = {}) {
  const wrapper = mount(componente, { attachTo: document.body, ...opcoes })
  montados.push(wrapper)
  return wrapper
}

export function desmontarTodos() {
  montados.splice(0).forEach(wrapper => wrapper.unmount())
  document.body.innerHTML = ''
}
