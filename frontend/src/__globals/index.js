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

  setTimeout(() => {
    $('.container-popup').css('display', 'flex')
  }, 1000)
  $('.container-popup .btn-close').click(event => {
    window.setCookie('popup_view', '1', 1) // 20s em dias -> 0.000231481
    $('.container-popup').remove()
  })
})
