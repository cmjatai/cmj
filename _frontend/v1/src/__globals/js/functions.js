
import dateFormat from 'dateformat'

window.dateFormat = dateFormat

window.removeTinymce = function () {
  while (window.tinymce.editors && window.tinymce.editors.length > 0) {
    window.tinymce.remove(window.tinymce.editors[0])
  }
}

window.initTextRichEditor = function (elements, readonly = false) {
  window.removeTinymce()
  const configTinymce = {
    selector: elements === null || elements === undefined ? 'textarea' : elements,
    /*
    forced_root_block: 'div',
    forced_root_block_attrs: {
      class: 'd-inline-block'
    },
    */
    plugins: 'lists table code link',
    min_height: 500,
    language: 'pt_BR',
    menubar: 'edit view format table tools',
    toolbar: 'undo redo | styles | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link',
    license_key: 'gpl'
  }
  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }
  window.tinymce.init(configTinymce)
}

window.refreshSelectPicker = function () {
  $('.selectpicker').selectpicker()
    .on('show.bs.select', function (event) {
      $('html, body').animate(
        {
          scrollTop:
            $(event.target.form).offset().top - '20' // - window.innerHeight / 9
        },
        500
      )
    })
}

window.refreshDatePicker = function () {
  $.datepicker.setDefaults($.datepicker.regional['pt-BR'])
  $('.dateinput').datepicker({
    beforeShow: function () {
      setTimeout(() => {
        $('.ui-datepicker').css('z-index', 3)
      }, 500)
    }

  })

  let dateinput = document.querySelectorAll('.dateinput')
  _.each(dateinput, function (input, index) {
    input.setAttribute('autocomplete', 'off')
  })
}

window.setCookie = function (cookieName, cookieValue, nDays) {
  let today = new Date()
  let expire = new Date()
  if (nDays === null || nDays === 0) nDays = 1
  expire.setTime(today.getTime() + 3600000 * 24 * nDays)
  document.cookie = cookieName + '=' + escape(cookieValue) +
    '; Path=/; Expires=' + expire.toGMTString()
}

window.getCookie = function (name) {
  var cookieValue = null
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';')
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i])
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

window.refreshMask = function () {
  $('.telefone').mask('(99) 99999-9999', { placeholder: '(__) ____ -____' })
  $('.cpf').mask('000.000.000-00', { placeholder: '___.___.___-__' })
  $('.cep').mask('00000-000', { placeholder: '_____-___' })
  $('.rg').mask('0.000.000', { placeholder: '_.___.___' })
  $('.titulo_eleitor').mask('0000.0000.0000.0000', {
    placeholder: '____.____.____.____'
  })
  $('.dateinput').mask('00/00/0000', { placeholder: '__/__/____' })
  $('.hora, input[name=hora_inicio], input[name=hora_fim], input[name=hora]').mask('00:00', {
    placeholder: 'hh:mm'
  })
  $('.hora_hms').mask('00:00:00', { placeholder: 'hh:mm:ss' })
  $('.timeinput').mask('00:00:00', { placeholder: 'hh:mm:ss' })
  $('.cronometro').mask('00:00:00', { placeholder: 'hh:mm:ss' })
  $('.datetimeinput').mask('00/00/0000 00:00:00', { placeholder: '__/__/____ hh:mm:ss' })
  $('.decimalinput').mask('#.##0,00', {
    reverse: true,
    translation: {
      '#': {
        pattern: /-|\d/,
        recursive: true
      },
      '0': {
        pattern: /[\d-]/,
        optional: false
      }
    },
    onChange: function (value, e) {
      e.target.value = value.replace(/(?!^)-/g, '').replace(/^\./, '').replace(/^-\./, '-')
    }
  })
}

window.isElementInViewport = function (el) {
  if (typeof jQuery === 'function' && el instanceof window.jQuery) {
    el = el[0]
  }
  let rect = el.getBoundingClientRect()
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  )
}

window.styleWithEndNameClass = function (endNameClass, attr, value = undefined) {
  for (var s = 0; s < document.styleSheets.length; s++) {
    var rules = document.styleSheets[s].rules || document.styleSheets[s].cssRules
    for (var r = 0; r < rules.length; r++) {
      if (rules[r].selectorText !== undefined && rules[r].selectorText.endsWith(endNameClass)) {
        if (value === undefined) {
          return rules[r].style[attr]
        }
        rules[r].style[attr] = value
      }
    }
  }
}

window.ContainerFirst = function () {
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
      first.removeClass('container-first')
    }
  } else {
    first.removeClass('.container-first')
    first.css('height', '')
    first.find('.painel-corte').remove()
  }
}

window.copyInputClipboard = function () {
  var copyText = document.getElementById('input-copy-clipboard')
  copyText.select()
  copyText.setSelectionRange(0, 99999)
  document.execCommand('copy')
}
