// Apoio aos testes dos componentes base (docs/specs/v8/componentes.md).
import fs from 'fs'
import path from 'path'
import { mount } from '@vue/test-utils'

export const RAIZ = path.resolve(__dirname, '../..')
export const PASTA = path.join(RAIZ, 'src/componentes')
export const OFICIAL = path.join(RAIZ, 'src/css/temas/oficial')

// Cada componente base e o prefixo das partes do Reka UI que ele usa.
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
  GrupoEtiquetas: 'TagGroup'
}

// Componentes que só exibem: não têm valor a devolver por v-model nem evento.
export const SO_EXIBICAO = ['Dica', 'Rotulo']

// Os arquivos CSS do oficial onde ficam as classes dos componentes.
export const CSS_DOS_COMPONENTES = ['primitivos.css', 'campos.css']

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
