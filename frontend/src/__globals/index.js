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

window.autorModal()
window.refreshMask()
window.refreshDatePicker()
window.initTextRichEditor('texto-rico')
// initTinymce
// import './2018/themes/dezembrolaranja/app.scss'





$(function () {
  
  let sidebarCmjCookie = window.localStorage.getItem('sidebarCmjCookie')
  if (sidebarCmjCookie !== undefined) {
    $("#wrapper").toggleClass(sidebarCmjCookie);
    $(".container").toggleClass(sidebarCmjCookie);
  }
  let toggleWrapper = function (event) {
      if (!$("#wrapper").hasClass('toggled')) {
        window.localStorage.setItem('sidebarCmjCookie', 'toggled')
        $(".canais-absolute .box").off('click')
      }
      else {
        window.localStorage.setItem('sidebarCmjCookie', '')
        $(".canais-absolute .box").click(toggleWrapper)
      }

      $("#wrapper").toggleClass("toggled");
      $(".container").toggleClass("toggled");
  
    event.preventDefault();
  }
  $("#menu-toggle, .canais-absolute .box").click(function (event) {
    toggleWrapper(event)
  });
  $('[data-toggle="popover"]').popover({
  trigger: 'focus'
  })
})

