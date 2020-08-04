import '@fortawesome/fontawesome-free/css/all.css'
// import '@fortawesome/fontawesome-free/js/all.js'

import 'bootstrap'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'
import 'webpack-jquery-ui/datepicker'
import 'jquery-ui/ui/i18n/datepicker-pt-BR'

import 'jquery-ui-themes/themes/pepper-grinder/jquery-ui.min.css'

import 'tinymce/tinymce'
import './2018/js/tinymce/lang/pt_BR.js'

import 'tinymce/themes/modern'
import 'tinymce/plugins/table'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/code'
import 'tinymce/plugins/colorpicker'

import 'jquery-mask-plugin'

import './2018/scss/app.scss'

import './2018/js/image_cropping'
import './2018/js/functions'

import './2018/js/app_cmj'

// eslint-disable-next-line
require('imports-loader?window.jQuery=jquery!./2018/js/jquery.runner.js')

window.$ = $
window.jQuery = $

window.AltoContraste()
window.autorModal()
window.refreshMask()
window.refreshDatePicker()
window.initTextRichEditor('texto-rico')
// initTinymce
// import './2018/themes/dezembrolaranja/app.scss'

$(function () {
  /* let toggleWrapper = function (event) {
    if (!$("#wrapper").hasClass('toggled')) {
      window.localStorage.setItem('sidebarCmjCookie', 'toggled')
      //$(".canais-absolute .box").off('click')
    }
    else {
      window.localStorage.setItem('sidebarCmjCookie', '')
      //$(".canais-absolute .box").click(toggleWrapper)
    }

    $("#wrapper").toggleClass("toggled");
    //$(".container").toggleClass("toggled");

    event.preventDefault();
  }

  $("#menu-toggle").click(function (event) {
    toggleWrapper(event)
  });

  let sidebarCmjCookie = window.localStorage.getItem('sidebarCmjCookie')
  if (sidebarCmjCookie !== undefined) {
    $("#wrapper").toggleClass(sidebarCmjCookie);
    //$(".container").toggleClass(sidebarCmjCookie);
    //$(".canais-absolute .box").off('click')
  } */

  $('[data-toggle="popover"]').popover({
    trigger: 'focus'
  })

  $('.copylink').click(event => {
    var $temp = $('<input>')
    $('body').append($temp)
    $temp.val(event.target.getAttribute('data_href')).select()
    document.execCommand('copy')
    $temp.remove()
  })
})

$(function () {
  // popups

  setTimeout(() => {
    $('.container-popup').css('display', 'flex')
  }, 500)

  $('#carousel-popup .carousel-item .click-item').click(event => {
    let pk = event.currentTarget.getAttribute('pk')
    let href = event.currentTarget.getAttribute('href')

    window.setCookie('popup_closed', '1', 0.006944444) // Caso o usuário clique em um popup, fica 10min sem mostrar popups
    window.setCookie(`popup_viewed_${pk}`, pk, 0.2) // Caso o usuário clique em um popup, fica 2h24min sem mostrar esse popup

    setTimeout(() => {
      document.location = `${href}?popup=1`
    }, 500)

    // DEV
    // window.setCookie('popup_closed', '1', 0.000231481) // Caso o usuário clique em um popup, fica 20s sem mostrar popups
    // window.setCookie(`popup_viewed_${pk}`, pk, 0.000462963) // Caso o usuário clique em um popup, 40s sem mostrar esse popup
  })

  $('.container-popup .btn-close').click(event => {
    window.setCookie('popup_closed', '1', 0.2) // 20s -> 0.000231481d // 2h24min -> 0.1d
    $('.container-popup').remove()

    // DEV
    // window.setCookie('popup_closed', '1', 0.001388889) // 2min
  })
})
