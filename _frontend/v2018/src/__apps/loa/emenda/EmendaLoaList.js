export default class EmendaLoaList {
  constructor (container) {
    this.container = container
    this.form = container.find('form')
    this.init()
  }

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

  init () {
    const form = this.form
    const formData = new FormData(form[0])
    const formProps = {}

    for (const [key, value] of formData.entries()) {
      if (key in formProps) {
        if (!Array.isArray(formProps[key])) {
          formProps[key] = [formProps[key]]
        }
        formProps[key].push(value)
      } else {
        if (value !== '') {
          formProps[key] = value
        }
      }
    }

    delete formProps.agrupamento
    delete formProps.tipo_agrupamento
    delete formProps.pdf

    // Função auxiliar para capturar os dados relevantes de filtro
    const getFilterData = () => {
      const formData = new FormData(form[0])
      const parlamentares = formData.getAll('parlamentares')
      const fase = formData.getAll('fase')
      const finalidade = formData.get('finalidade')
      const tipo = formData.getAll('tipo')

      return {
        parlamentares: parlamentares.length > 0 ? parlamentares : [],
        fase: fase.length > 0 ? fase : [],
        finalidade: finalidade !== '' ? [finalidade] : [],
        tipo: tipo.length > 0 ? tipo : []
      }
    }

    // Verifica se há filtros selecionados no formulário atual
    if (this.isObjectEmpty(formProps)) {
      try {
        const lsJson = localStorage.getItem('portalcmj_emendaloa_filter')

        // Verifica se existe dados salvos e se são válidos
        if (lsJson) {
          const lsData = JSON.parse(lsJson)

          if (!this.isObjectEmpty(lsData)) {
            _.forOwn(lsData, (value, key) => {
              _.forEach(form.find(`input[name="${key}"]`), (item) => {
                if ((Array.isArray(value) && value.includes(item.value)) || value === item.value) {
                  item.checked = true
                  $(`label[for="${item.id}"] span`).addClass('active')
                } else if (!Array.isArray(value)) {
                  item.value = value
                } else if (Array.isArray(value) && value.length > 0 && item.type === 'text') {
                  // Tratamento específico para campos de texto que foram salvos como array
                  item.value = value[0]
                }
              })
            })

            // Verifica se realmente tem filtros aplicados antes de submeter o form
            const filterData = getFilterData()
            if (!this.isObjectEmpty(filterData)) {
              window.loadingCMJ('Atualizando listagem...')
              form.submit()
            }
          }
        }
      } catch (e) {
        console.error('Erro ao recuperar filtros do localStorage:', e)
        // Limpa localStorage se houver erro no JSON
        localStorage.removeItem('portalcmj_emendaloa_filter')
      }
    } else {
      // Salva filtros atuais no localStorage
      const filterData = getFilterData()
      localStorage.setItem('portalcmj_emendaloa_filter', JSON.stringify(filterData))
    }

    // Simplifica a função de mudança para usar getFilterData
    let changeAction = (event) => {
      const filterData = getFilterData()
      localStorage.setItem('portalcmj_emendaloa_filter', JSON.stringify(filterData))

      window.loadingCMJ('Atualizando listagem...')
      form.submit()
    }

    const sAgrup = form.find('input[type="checkbox"][name="agrupamento"]')
    const rTipoAgrup = form.find('input[type="radio"][name="tipo_agrupamento"]')
    sAgrup.change((event) => {
      if (sAgrup.filter(':checked').length === 0) {
        rTipoAgrup.filter('[value="sem_registro"]').prop('checked', true)
      }
    }).change()

    rTipoAgrup
      .change((event) => {
        if (event.target.checked && event.target.value === 'sem_registro') {
          sAgrup.not('[value="despesa__unidade"]').prop('disabled', true).prop('checked', false).parent().addClass('d-none')
          sAgrup.filter('[value="despesa__unidade"]').prop('disabled', false).parent().removeClass('d-none')
          sAgrup.filter('[value="despesa__unidade"]').prop('checked', true)
        } else if (event.target.checked) {
          sAgrup.prop('disabled', false).parent().removeClass('d-none')
          if (sAgrup.filter(':checked').length === 0) {
            if (sAgrup.length > 1) {
              $(sAgrup[1]).prop('checked', true)
            } else if (sAgrup.length > 0) {
              $(sAgrup[0]).prop('checked', true)
            }
          }
        } else {
          sAgrup.prop('disabled', false).parent().removeClass('d-none')
        }
      }).change()

    form
      .find('#div_id_parlamentares input[type="checkbox"]')
      .change((event) => {
        changeAction()
      })
    form
      .find('button[type="button"]')
      .click((event) => {
        changeAction()
      })
    form
      .find('input[type="submit"]')
      .click((event) => {
        window.loadingCMJ('Gerando Listagem em PDF...')
      })
    form.keypress((event) => {
      if (event.keyCode === 13) {
        event.preventDefault()
        return false
      }
    })
  }
}
