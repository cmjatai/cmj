import skinTinymce from 'tinymce-light-skin'

window.removeTinymce = function () {
  while (window.tinymce.editors.length > 0) {
    window.tinymce.remove(window.tinymce.editors[0])
  }
}

window.initTextRichEditor = function (elements, readonly = false) {
  window.removeTinymce()
  let configTinymce = {
    'force_br_newlines': false,
    'force_p_newlines': false,
    'forced_root_block': '',
    'content_style': skinTinymce.contentStyle,
    'skin': false,
    'plugins': ['lists table code'],
    'menubar': 'file edit view format table tools',
    toolbar: 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent',
    'tools': 'inserttable',
    min_height: 200

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

window.autorModal = function () {
  $(function () {
    var dialog = $('#modal_autor').dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 340,
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

      function clean_if_exists (fieldname) {
        if ($(fieldname).length > 0) {
          $(fieldname).val('')
        }
      }

      clean_if_exists('#id_autor')
      clean_if_exists('#id_autoria__autor')
    })

    $('#button-id-pesquisar').click(function () {
      $('#q').val('')
      $('#div-resultado')
        .children()
        .remove()
      $('#modal_autor').dialog('open')
      $('#selecionar').attr('hidden', 'hidden')
    })

    $('#pesquisar').click(function () {
      var name_in_query = $('#q').val()
      // var q_0 = "q_0=nome__icontains"
      // var q_1 = name_in_query
      // query = q_1

      $.get('/api/autor?q=' + name_in_query, function (data) {
        $('#div-resultado')
          .children()
          .remove()
        if (data.pagination.total_entries === 0) {
          $('#selecionar').attr('hidden', 'hidden')
          $('#div-resultado').html(
            "<span class='alert'><strong>Nenhum resultado</strong></span>"
          )
          return
        }

        var select = $(
          '<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>'
        )

        data.results.forEach(function (item) {
          select.append(
            $('<option>')
              .attr('value', item.value)
              .text(item.text)
          )
        })

        $('#div-resultado')
          .append('<br/>')
          .append(select)
        $('#selecionar').removeAttr('hidden', 'hidden')

        if (data.pagination.total_pages > 1) {
          $('#div-resultado').prepend(
            '<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>'
          )
        }

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

  /* function get_nome_autor(fieldname) {
    if ($(fieldname).length > 0) { // se campo existir
      if ($(fieldname).val() != "") { // e não for vazio
        var id = $(fieldname).val();
        $.get("/proposicao/get-nome-autor?id=" + id, function(data, status){
            $("#nome_autor").text(data.nome);
        });
      }
    }
  }

  get_nome_autor("#id_autor");
  get_nome_autor("#id_autoria__autor"); */
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
