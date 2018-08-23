import jQuery from 'jquery'
import './functions'

window.$ = window.jQuery = jQuery

window.Gallery = function () {
  let instance
  // eslint-disable-next-line
  let galerias

  if (!(this instanceof window.Gallery)) {
    if (!instance) {
      instance = new window.Gallery()
    }
    return instance
  }
  instance = this
  // eslint-disable-next-line
  window.Gallery = function () {
    return instance
  }

  instance.intervalThumb = function () {
    let func = function () {
      instance.galerias.each(function (idxGaleria, _galeria) {
        let width = 0
        let galeria = $(_galeria)

        galeria.find('.gallery-item').each(function (index, item) {
          width = width + item.offsetWidth
        })

        if (_galeria.thumbWidthOld === undefined) {
          _galeria.thumbWidthOld = width
        } else {
          if (_galeria.thumbWidthOld === width) {
            return
          }
        }
        _galeria.thumbWidthOld = width
        galeria.find('.thumb-scroll').css('width', (width + 12) + 'px')
      })
    }
    func()
    setInterval(function () {
      func()
      // TODO: encerrar interval depois n interações sem mudanças
      // TODO: Avaliar necessidade de resize devido a responsividade (em dispositivos com mudanças de vertical/horizontal, por exemplo.)
    }, 2000)
  }
  instance.resize = function (e, ajustaShowImage = true) {
    instance.galerias.each(function (idxGaleria, _galeria) {
      let galeria = $(_galeria)
      let height
      let strHeight
      if (galeria.closest('.albuns-show-gallery').length === 1) {
        height = window.innerHeight
        strHeight = 'height'
      } else {
        height = (window.innerWidth > window.innerHeight ? window.innerHeight * 0.9 : window.innerWidth)
        if (window.innerWidth > window.innerHeight) {
          strHeight = 'height'
        } else {
          strHeight = 'min-height'
        }
      }

      let inner = galeria.find('.gallery-inner').css(strHeight, height + 'px')
      let galleryShow = galeria.find('.gallery-show').css(strHeight, height - galeria.find('.gallery-thumbnails')[0].offsetHeight)
      galleryShow.css('width', inner[0].offsetWidth + 'px')

      if (ajustaShowImage) {
        instance.ajustaShowImage(galleryShow.find('img')[0])
      }
    })
  }
  instance.ajustaShowImage = function (img) {
    let divImage = img.parentElement
    divImage.style.padding = ''
    divImage.style.paddingTop = ''

    img.style.width = 'auto'
    img.style.height = 'auto'

    if (divImage.offsetHeight > divImage.offsetWidth) {
      divImage.style.paddingTop = (divImage.offsetHeight - img.height) / 2 + 'px'
    } else {
      if (divImage.parentElement.offsetWidth !== divImage.parentElement.parentElement.offsetWidth) {
        divImage.style.padding = divImage.offsetHeight * 0.04 + 'px'
        divImage.style.paddingTop = (divImage.offsetHeight - img.height) / 2 + 'px'
      } else {

      }
    }
  }
  instance.updateEventTouch = function (_show) {
    let show = _show[0]

    show.addEventListener('touchstart', function (e) {
      instance.touchStartX = e.touches[0].clientX
      instance.touchStartTime = e.timeStamp
    })
    show.addEventListener('touchend', function (e) {
      let _this = this
      let x = instance.touchLastX
      let taxa = (x - instance.touchStartX) / this.offsetWidth * 100
      let it = x >= instance.touchStartX ? this.previousElementSibling : this.nextElementSibling

      let base = e.timeStamp - instance.touchStartTime < 500 ? 7 : 30

      if (it && it.classList.contains('gallery-show') && (taxa > base || taxa < -base)) {
        $(this).animate({
          'left': (x - instance.touchStartX) > 0 ? '100%' : '-100%'
        }, 200)

        $(it).animate({
          'left': 0
        }, 200, function () {
          $(_this).off('touchstart').off('touchend').off('touchmove')
          $(_this).removeClass('active')
          $(it).addClass('active')
          // instance.recreateNextPrevious($(next[0].data))
          $(it.data).trigger('click')
        })
      } else {
        if (it && it.classList.contains('gallery-show')) {
          $(it).animate({
            'left': (x - instance.touchStartX) > 0 ? '-100%' : '100%'
          }, 200)
        }

        $(this).animate({
          'left': 0
        }, 200, function () {
          // instance.recreateNextPrevious(_this.data)
        })
      }
    })
    show.addEventListener('touchmove', function (e) {
      let x = e.touches[0].clientX
      instance.touchLastX = x
      let it = x >= instance.touchStartX ? this.previousElementSibling : this.nextElementSibling
      let taxa = (x - instance.touchStartX) / this.offsetWidth * 100
      if ((taxa > 3 && taxa <= 100) || (taxa < -3 && taxa >= -100)) {
        this.style.left = taxa + '%'
        if (it && it.classList.contains('gallery-show')) {
          it.style.left = (x >= instance.touchStartX ? -(100 - taxa) : 100 + taxa) + '%'
        }
      } else {
        this.style.left = 0
      }
    })
  }
  instance.recreateNextPrevious = function (itemSelecionado) {
    instance.galerias.each(function (idxGaleria, _galeria) {
      let galeria = $(_galeria)

      let view = galeria.find('.gallery-show.active')

      let shows = galeria.find('.gallery-show')
      shows.clearQueue()
      view.clearQueue()
      shows.stop()
      view.stop()

      if (itemSelecionado === undefined) {
        shows.each(function (idx, _item) {
          _item.style.height = view[0].style.height
          _item.style.width = view[0].style.width
        })
        return
      }

      let previous = []
      let next = []
      let size = 4
      let flagPn = false
      for (let i = 0; i < shows.length; i++) {
        if (shows[i] === view[0]) {
          flagPn = true
          continue
        }
        (flagPn ? next : previous).push(shows[i])
      }

      if (itemSelecionado.previousElementSibling) {
        while (previous.length < size) {
          let vc = view[0].cloneNode(true)
          vc.style.left = '100%'
          vc.style.width = view[0].offsetWidth + 'px'
          vc.classList.remove('active')
          previous.push(vc)
          view[0].parentNode.insertBefore(vc, view[0])
        }
      } else {
        for (let i = 0; i < previous.length; i++) {
          previous[i].remove()
        }
      }

      if (itemSelecionado.nextElementSibling) {
        while (next.length < size) {
          let vc = view[0].cloneNode(true)
          vc.style.left = '100%'
          vc.style.width = view[0].offsetWidth + 'px'
          vc.classList.remove('active')
          next.unshift(vc)
          view[0].parentNode.insertBefore(vc, view[0].nextSibling)
        }
      } else {
        for (let i = 0; i < next.length; i++) {
          next[i].remove()
        }
      }

      let left = -100
      let p = itemSelecionado.previousElementSibling
      for (let i = previous.length - 1; i > -1; i--) {
        if (!p || i > size - 1) {
          previous[i].remove()
          continue
        }
        previous[i].style.left = left + '%'
        left -= 100
        $(previous[i]).find('img')[0].src = $(p).find('img')[0].src // getAttribute('data-src')
        previous[i].data = p

        if (p.children.length === 2) {
          let texto = p.children[1]
          let textoClone = texto.cloneNode(true)
          $(previous[i]).find('.show-texto').replaceWith(textoClone)
        }

        p = p.previousElementSibling
      }

      left = 100
      let n = itemSelecionado.nextElementSibling
      for (let i = 0; i < next.length; i++) {
        if (!n || i > size - 1) {
          next[i].remove()
          continue
        }
        next[i].style.left = left + '%'
        left += 100
        $(next[i]).find('img')[0].src = $(n).find('img')[0].src // getAttribute('data-src')
        next[i].data = n

        if (n.children.length === 2) {
          let texto = n.children[1]
          let textoClone = texto.cloneNode(true)
          $(next[i]).find('.show-texto').replaceWith(textoClone)
        }

        n = n.nextElementSibling
      }

      let preloads = next.concat(previous)
      let preloadImgs = function (i) {
        let progress = $(preloads[i]).find('.progress')
        if (i < preloads.length - 1) {
          setTimeout(function () {
            let img = $(preloads[i]).find('img')[0]
            progress.css('width', img.style.width)
            progress.css('left', img.offsetLeft + 'px')
            progress.css('top', img.offsetTop + img.offsetHeight - 2 + 'px')
            progress.removeClass('invisible')
          }, 100)
        }

        if ($(preloads[i].data).find('img').length === 1) {
          $(preloads[i]).find('img').one('load', function () {
            instance.ajustaShowImage(this)
            progress.addClass('invisible')
            if (i < preloads.length - 1) {
              preloadImgs(i + 1)
            }
          }).attr('src', $(preloads[i].data).find('img')[0].getAttribute('data-src'))
        }
      }

      if (preloads.length > 0) {
        preloadImgs(0)
      }
    })
  }
  instance.addEventClick = function () {
    instance.galerias.each(function (idxGaleria, _galeria) {
      let galeria = $(_galeria)
      galeria.find('.gallery-item').click(function (event) {
        let _this = this
        galeria.find('.gallery-item').removeClass('active')
        $(_this).addClass('active')
        let showActive = galeria.find('.gallery-show.active')

        if (showActive.length === 0) {
          showActive = $(galeria.find('.gallery-show')[0]).addClass('active').css('left', 0)
        }

        instance.updateEventTouch(showActive)
        showActive[0].data = _this

        if (_this.children.length === 2) {
          let texto = _this.children[1]
          let textoClone = texto.cloneNode(true)
          showActive.find('.show-texto').replaceWith(textoClone)
        }
        $(_this.parentElement.parentElement).animate({
          scrollLeft: _this.offsetLeft - showActive.width() / 2 + _this.offsetWidth / 2
        }, 300)

        let thumb = _this.children[0]

        let img = showActive.find('.show-image img')[0]
        let progress = showActive.find('.progress')

        let imgHeight = img.height

        if (!img.src.endsWith(thumb.getAttribute('data-src'))) {
          setTimeout(function () {
            img.src = thumb.src
            img.style.height = imgHeight + 'px'
            img.style.width = (imgHeight * (thumb.width / thumb.height)) + 'px'
            progress.css('width', img.style.width)
            progress.css('left', img.offsetLeft + 'px')
            progress.css('top', img.offsetTop + img.offsetHeight - 2 + 'px')
            progress.removeClass('invisible')
          }, 100)

          setTimeout(function () {
            $(img).one('load', function () {
              progress.addClass('invisible')
              instance.ajustaShowImage(img)
              instance.recreateNextPrevious(_this)
            }).attr('src', thumb.getAttribute('data-src'))
          }, 200)
        } else {
          progress.addClass('invisible')
          instance.ajustaShowImage(img)
          instance.recreateNextPrevious(_this)
        }
      })

      galeria.find('.gallery-item:first-child').trigger('click')

      galeria.find('.path-next a').click(function () {
        let view = galeria.find('.gallery-show.active')
        let next = view.next()

        if (!next.hasClass('gallery-show')) {
          return false
        }

        $(next[0].data.parentElement.parentElement).animate({
          scrollLeft: next[0].data.offsetLeft - view.width() / 2 + next[0].data.offsetWidth / 2
        }, 300)

        view.animate({
          'left': view.width() * -1
        }, 300)

        next.animate({
          'left': 0
        }, 400, function () {
          view.removeClass('active')
          next.addClass('active')
          // instance.recreateNextPrevious($(next[0].data))
          $(next[0].data).trigger('click')
        })
        return false
      })

      galeria.find('.path-previous a').click(function () {
        let view = galeria.find('.gallery-show.active')
        let prev = view.prev()

        if (!prev.hasClass('gallery-show')) {
          return false
        }

        $(prev[0].data.parentElement.parentElement).animate({
          scrollLeft: prev[0].data.offsetLeft - view.width() / 2 + prev[0].data.offsetWidth / 2
        }, 300)

        view.animate({
          'left': view.width()
        }, 300)

        prev.animate({
          'left': 0
        }, 400, function () {
          view.removeClass('active')
          prev.addClass('active')
          // instance.recreateNextPrevious($(prev[0].data))
          $(prev[0].data).trigger('click')
        })
        return false
      })
    })
  }

  instance.init = function () {
    instance.galerias = $('.container-gallery')
    instance.intervalThumb()

    instance.resize()
    window.onresize = instance.resize
    $('.container-gallery').on('resize', instance.resize)

    instance.addEventClick()
  }
  // para ser reusada sem recriar objeto Gallery deve ser comentado
  // instance.init()
}

window.autorModal = function () {
  $(function () {
    let dialog = $('#modal_autor').dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 300,
      show: {
        effect: 'blind',
        duration: 500
      },
      hide: {
        effect: 'explode',
        duration: 500
      }
    })

    $('#button-id-limpar').click(function () {
      $('#nome_autor').text('')

      function cleanIfExists (fieldname) {
        if ($(fieldname).length > 0) {
          $(fieldname).val('')
        }
      }
      cleanIfExists('#id_autor')
      cleanIfExists('#id_autoria__autor')
    })

    $('#button-id-pesquisar').click(function () {
      $('#q').val('')
      $('#div-resultado').children().remove()
      $('#modal_autor').dialog('open')
      $('#selecionar').attr('hidden', 'hidden')
    })

    $('#pesquisar').click(function () {
      let query = $('#q').val()

      $.get('/api/autor?q=' + query, function (data, status) {
        $('#div-resultado').children().remove()
        if (data.pagination.total_entries === 0) {
          $('#selecionar').attr('hidden', 'hidden')
          $('#div-resultado').html('<span class="alert"><strong>Nenhum resultado</strong></span>')
          return
        }

        let select = $('<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>')

        data.results.forEach(function (item, index) {
          select.append($('<option>').attr('value', item.value).text(item.text))
        })

        $('#div-resultado').append('<br/>').append(select)
        $('#selecionar').removeAttr('hidden', 'hidden')

        $('#selecionar').click(function () {
          let res = $('#resultados option:selected')
          let id = res.val()
          let nome = res.text()

          $('#nome_autor').text(nome)

          // MateriaLegislativa pesquisa Autor via a tabela Autoria
          if ($('#id_autoria__autor').length) {
            $('#id_autoria__autor').val(id)
          }
          // Protocolo pesquisa a própria tabela de Autor
          if ($('#id_autor').length) {
            $('#id_autor').val(id)
          }
          dialog.dialog('close')
        })
      })
    })
  })
}

window.OptionalCustomFrontEnd = function () {
  // Adaptações opcionais de layout com a presença de JS.
  // Não implementar customizações que a funcionalidade que fique dependente.
  let instance
  if (!(this instanceof window.OptionalCustomFrontEnd)) {
    if (!instance) {
      instance = new window.OptionalCustomFrontEnd()
    }
    return instance
  }
  instance = this
  window.OptionalCustomFrontEnd = function () {
    return instance
  }
  instance.customCheckBoxAndRadio = function () {
    $('[type=radio], [type=checkbox]').each(function () {
      let _this = $(this)
      let _controls = _this.closest('.controls')
      _controls && _controls.find(':file').length === 0 && !_controls.hasClass('controls-radio-checkbox') && _controls.addClass('controls-radio-checkbox')
      _controls.find(':file').length > 0 && _controls.addClass('controls-file')
    })
  }
  instance.customCheckBoxAndRadioWithoutLabel = function () {
    $('[type=radio], [type=checkbox]').each(function () {
      let _this = $(this)
      let _label = _this.closest('label')

      if (_label.length) {
        return
      }

      if (this.id) {
        _label = $('label[for=' + this.id + ']')
      } else {
        _label = $('<label/>').insertBefore(this)
      }

      if (_label.length) {
        _label.addClass('checkbox-inline')
        _label.prepend(_this)
        _this.checkbox()
      }
    })
  }
  instance.init = function () {
    this.customCheckBoxAndRadio()
    this.customCheckBoxAndRadioWithoutLabel()
  }
  instance.init()
}

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

        console.log(quociente + ' = ' + resto)

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
window.TrechoSearch = function (opts) {
  $(function () {
    let ctsClear = $('body').children('.cts') // Container Trecho Search
    if (ctsClear.length > 0) {
      $(ctsClear).remove()
    }

    $("input[name='endereco']").each(function () {
      let input = $(this)
      let inputRow = $(input.closest('.row'))
      let cts = $('<div class="cts"/>')
      let qOld = input.val()
      let qNew = input.val()
      let intervalKeyPress = null
      input.after(cts)

      let ctsShow = function () {
        let rowPosition = inputRow[0].getBoundingClientRect()
        let inputPosition = input[0].getBoundingClientRect()
        cts.animate({
          'top': inputPosition.bottom,
          'left': inputPosition.left + 7,
          'right': rowPosition.right - rowPosition.width
        }, 400)
      }
      let ctsHidden = function () {
        cts.css('visibility', 'hidden')
      }

      $(window).resize(ctsHidden)
      $(window).scroll(ctsHidden)

      let zoomListeners = [ctsHidden]
      let lastWidth = 0
      let pollZoomFireEvent = function () {
        let widthNow = $(window).width()
        if (lastWidth === widthNow) return
        lastWidth = widthNow
        // Length changed, user must have zoomed, invoke listeners.
        for (let i = zoomListeners.length - 1; i >= 0; --i) {
          zoomListeners[i]()
        }
      }
      setInterval(pollZoomFireEvent, 300)

      let flagNewkeypress = false
      let flagGetRunAjax = false
      let keyUpEndereco = function () {
        if (qOld !== qNew) {
          qOld = qNew
          return
        }
        if (!flagNewkeypress) {
          return
        }
        flagNewkeypress = false

        if (flagGetRunAjax) {
          return
        }
        flagGetRunAjax = true

        let formData = {
          'q': qNew,
          'format': 'json'
        }
        $.get(opts.api_rest_list, formData).done(function (data) {
          cts.html('')
          ctsShow()
          cts.css('visibility', (data.results.length === 0 ? 'hidden' : 'visible'))

          $.each(data.results, function (index, itemData) {
            let its = $('<div class="its"/>') // Item de Trecho Search
            its.append(itemData.display)
            cts.append(its)

            its.on('click', function (event, setDataEndereco) {
              let pk = this.data
              let formData = {
                'format': 'json'
              }
              let url = opts.api_rest_retrieve
              url = url.replace('0', pk)
              $.get(url, formData, function (retrivieData) {
                $("input[name='trecho']").val(pk)
                if (setDataEndereco !== undefined && setDataEndereco) {
                  $("input[name='endereco']").attr('data', retrivieData.tipo_descricao + ' ' + retrivieData.logradouro_descricao)
                } else {
                  $("input[name='endereco']").val(retrivieData.tipo_descricao + ' ' + retrivieData.logradouro_descricao)
                }
                $("select[name='bairro']").val(retrivieData.bairro_id)
                $("input[name='cep']").val(retrivieData.cep[0])
                $("select[name='distrito']").val(retrivieData.distrito_id)
                $("select[name='regiao_municipal']").val(retrivieData.regiao_municipal_id)
                $("select[name='municipio']").val(retrivieData.municipio_id)
                $("select[name='uf']").val(retrivieData.uf)
              })
            })
            its[0].data = itemData.pk
          })
        }).always(function () {
          flagGetRunAjax = false
        })
      }
      input.on('keyup', function () {
        if (intervalKeyPress === null) {
          intervalKeyPress = setInterval(keyUpEndereco, 700)
        }
        flagNewkeypress = true
        qNew = input.val()
        if (qNew === qOld || qNew.length < 3) {
          cts.css('visibility', 'hidden')
        }
      }).on('blur', function () {
        let inputData = $(this).attr('data')
        if (inputData !== undefined && inputData !== '') {
          $(this).val(inputData)
        }

        setTimeout(function () {
          cts.css('visibility', 'hidden')
        }, 300)
      })
    })
  })
}

window.$(document).ready(function () {
  window.refreshDatePicker()
  window.refreshMask()
  window.autorModal()
  // initTinymce()
  window.OptionalCustomFrontEnd()
})
