// AppLOA.js

import EmendaLoaCRUD from './emenda/EmendaLoaCRUD'
import AgrupamentoCRUD from './agrupamento/AgrupamentoCRUD'

class AppLOA {
  constructor () {
    // Se precisar garantir que window.AppLOA exista para compatibilidade com scripts legados:
    if (typeof window !== 'undefined') {
      window.AppLOA = this
    }
    this.EmendaLoaCRUD = null
    this.AgrupamentoCRUD = null
  }

  run () {
    // Sua lógica de inicialização aqui
    // Ex: this.LoaCRUD();
    console.log('AppLOA inicializado')
    this.EmendaLoaCRUD = new EmendaLoaCRUD()
    this.AgrupamentoCRUD = new AgrupamentoCRUD()
  }

  // Exemplo de método convertido
  isObjectEmpty (obj) {
    let isEmpty = true
    _.forOwn(obj, (value, key) => {
      if ((Array.isArray(value) && value.length > 0)) {
        isEmpty = false
      } else if (!Array.isArray(value) && !['', null, undefined].includes(value)) {
        isEmpty = false
      }
    })
    return isEmpty
  }

  // Outros métodos da classe...
}

// Exporta uma instância única (Singleton)
export default new AppLOA()
