window.ImpressoEnderecamentoRenderer = function (opts) {
  $(function () {
    let ier = $('body').children('.ier')
    if (ier.length > 0) {
      $(ier).remove()
    }
    ier = $('<div class="ier"/>')
    let eb = $('<div class="etiqueta"/>')

    let form = $('form')
    form.after(ier)

    let resize = function (event) {
      let larguraPagina = parseFloat(form[0].elements['largura_pagina'].value)
      let alturaPagina = parseFloat(form[0].elements['altura_pagina'].value)
      let rotate = form[0].elements['rotate'].value === 'True'

      let razao = alturaPagina / larguraPagina
      let conversao = ier.width() / larguraPagina
      ier.height(ier.width() * razao)

      let margemEsquerda = parseFloat(form[0].elements[rotate ? 'margem_superior' : 'margem_esquerda'].value) * conversao
      let margemSuperior = parseFloat(form[0].elements[rotate ? 'margem_esquerda' : 'margem_superior'].value) * conversao

      let colunasfolha = parseInt(form[0].elements['colunasfolha'].value)
      let linhasfolha = parseInt(form[0].elements['linhasfolha'].value)

      let entreColunas = parseFloat(form[0].elements[rotate ? 'entre_linhas' : 'entre_colunas'].value) * conversao
      let entreLinhas = parseFloat(form[0].elements[rotate ? 'entre_colunas' : 'entre_linhas'].value) * conversao

      let larguraetiqueta = parseFloat(form[0].elements[rotate ? 'alturaetiqueta' : 'larguraetiqueta'].value) * conversao
      let alturaetiqueta = parseFloat(form[0].elements[rotate ? 'larguraetiqueta' : 'alturaetiqueta'].value) * conversao

      let totalEtiquetas = colunasfolha * linhasfolha

      let etiquetas = $('.ier .etiqueta')
      while (etiquetas.length < totalEtiquetas) {
        etiquetas.push(eb.clone())
        ier.append(etiquetas[etiquetas.length - 1])
      }
      while ($('.ier .etiqueta').length > totalEtiquetas) {
        $('.ier .etiqueta').last().remove()
      }
      etiquetas = $('.ier .etiqueta')
      etiquetas.width(larguraetiqueta)
      etiquetas.height(alturaetiqueta)

      for (let i = 0; i < etiquetas.length; i++) {
        let left = margemEsquerda
        let top = margemSuperior

        let quociente = i / colunasfolha | 0
        let resto = i % colunasfolha

        // console.debug(quociente + ' = ' + resto)

        if (resto > 0) {
          left += (resto) * entreColunas + (resto) * larguraetiqueta
        }
        if (quociente > 0) {
          top += (quociente) * entreLinhas + (quociente) * alturaetiqueta
        }

        etiquetas[i].style.left = left + 'px'
        if (rotate) {
          etiquetas[i].style.bottom = top + 'px'
        } else {
          etiquetas[i].style.top = top + 'px'
        }
      }
    }
    $(window).resize(resize)
    form.change(resize)
    $(window).trigger('resize')
  })
}
