import skinTinymce from 'tinymce-light-skin'

window.getCookie = function (name) {
  var cookieValue = null
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';')
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i])
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

window.refreshDatePicker = function () {
  $.datepicker.setDefaults($.datepicker.regional['pt-BR'])
  $('.dateinput').datepicker()
}

window.refreshMask = function () {
  $('.telefone').mask('(99) 9999-9999', {placeholder: '(__) ____ -____'})
  $('.cpf').mask('000.000.000-00', {placeholder: '___.___.___-__'})
  $('.cep').mask('00000-000', {placeholder: '_____-___'})
  $('.rg').mask('0.000.000', {placeholder: '_.___.___'})
  $('.titulo_eleitor').mask('0000.0000.0000.0000', {placeholder: '____.____.____.____'})
  $('.dateinput').mask('00/00/0000', {placeholder: '__/__/____'})
  $('.hora').mask('00:00', {placeholder: 'hh:mm'})
  $('.hora_hms').mask('00:00:00', {placeholder: 'hh:mm:ss'})
  $('.datetimeinput').mask('00/00/0000 00:00:00', {placeholder: '__/__/____ hh:mm:ss'})
  $('.timeinput').mask('00:00', {placeholder: 'hh:mm'})
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

window.removeTinymce = function () {
  while (window.tinymce.editors.length > 0) {
    window.tinymce.remove(window.tinymce.editors[0])
  }
}

window.initTinymce = function (elements, readonly = false) {
  window.removeTinymce()
  let configTinymce = {
    'force_br_newlines': false,
    'force_p_newlines': false,
    'forced_root_block': '',
    'content_style': skinTinymce.contentStyle,
    'skin': false,
    'plugins': ['table'],
    'toolbar': 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent',
    'tools': 'inserttable'
  }

  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }

  if (elements != null) {
    configTinymce['elements'] = elements
    configTinymce['mode'] = 'exact'
  } else {
    configTinymce['mode'] = 'textareas'
  }
  skinTinymce.use()
  window.tinymce.init(configTinymce)
}

window.AltoContraste = function () {
  let Contrast = {
    storage: 'contrastState',
    cssClass: 'contrast',
    currentState: null,
    check: checkContrast,
    getState: getContrastState,
    setState: setContrastState,
    toogle: toogleContrast,
    updateView: updateViewContrast
  }

  window.toggleContrast = function () {
    Contrast.toogle()
  }
  Contrast.check()

  function checkContrast () {
    this.updateView()
  }

  function getContrastState () {
    return localStorage.getItem(this.storage) === 'true'
  }

  function setContrastState (state) {
    localStorage.setItem(this.storage, '' + state)
    this.currentState = state
    this.updateView()
  }

  function updateViewContrast () {
    let body = document.body
    if (this.currentState === null) {
      this.currentState = this.getState()
    }
    if (this.currentState) {
      body.classList.add(this.cssClass)
    } else {
      body.classList.remove(this.cssClass)
    }
  }

  function toogleContrast () {
    this.setState(!this.currentState)
  }
}
window.AltoContraste()
