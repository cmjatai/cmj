import 'font-awesome/css/font-awesome.css'
import './2018/scss/app.scss'
import jQuery from 'jquery'
import 'bootstrap'

window.$ = window.jQuery = jQuery

// eslint-disable-next-line
function Gallery () {
  let instance
  // eslint-disable-next-line
  let galerias

  if (!(this instanceof Gallery)) {
    if (!instance) {
      instance = new Gallery()
    }
    return instance
  }
  instance = this
  // eslint-disable-next-line
  Gallery = function () {
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
            progress.removeClass('hidden')
          }, 100)
        }

        if ($(preloads[i].data).find('img').length === 1) {
          $(preloads[i]).find('img').one('load', function () {
            instance.ajustaShowImage(this)
            progress.addClass('hidden')
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
            progress.removeClass('hidden')
          }, 100)

          setTimeout(function () {
            $(img).one('load', function () {
              progress.addClass('hidden')
              instance.ajustaShowImage(img)
              instance.recreateNextPrevious(_this)
            }).attr('src', thumb.getAttribute('data-src'))
          }, 200)
        } else {
          progress.addClass('hidden')
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

// eslint-disable-next-line
function ContainerFirst () {
  let first = $('.container-first')

  if (first.height() > window.innerHeight) {
    first.css('height', window.innerHeight)
    let btn = first.find('.btn').click(function () {
      this.parentElement.remove()
      first.css('height', '')
      first.removeClass('container-first')
    })
    if (btn.length === 0) {
      first.css('height', '')
    }
  } else {
    first.removeClass('.container-first')
    first.css('height', '')
    first.find('.painel-corte').remove()
  }
}

window.ContainerFirst = ContainerFirst
window.Gallery = Gallery
