// import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/js/all.js'

import 'bootstrap'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'
import 'webpack-jquery-ui/datepicker'
import 'jquery-ui/ui/i18n/datepicker-pt-BR'

import 'jquery-ui-themes/themes/pepper-grinder/jquery-ui.min.css'

import 'tinymce/tinymce'
import './2021/js/tinymce/lang/pt_BR.js'

import 'tinymce/themes/modern'
import 'tinymce/plugins/table'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/code'
import 'tinymce/plugins/colorpicker'

import 'jquery-mask-plugin'
import './2021/js/image_cropping'
import './2021/js/functions'

import './2021/js/app_cmj'

const theme = window.document.currentScript.getAttribute('theme') || 'oficial'
require(`./2021/scss/themes/${theme}/global.scss`)
// eslint-disable-next-line

window.$ = $
window.jQuery = $
// initTinymce
// import './2018/themes/dezembrolaranja/app.scss'

$(function () {
  setTimeout(function () {
    window.AltoContraste()
    window.autorModal()
    window.refreshMask()
    window.refreshDatePicker()
    window.initTextRichEditor('texto-rico')

    $('a[data-social-sharing]').click(function (event) {
      event.preventDefault()
      let socialNetwork = $(this).data('social-sharing')
      let _height, _width
      switch (socialNetwork) {
        case 'facebook': _height = 436; _width = 626; break
        case 'whatsapp': _height = 591; _width = 617; break
        case 'twitter': _height = 300; _width = 600
      }
      let leftPosition = (window.screen.width / 2) - ((_width / 2) + 10)
      let topPosition = (window.screen.height / 2) - ((_height / 2) + 50)
      let stringSpecs = 'left=' + leftPosition + ',top=' + topPosition + ',toolbar=0,status=0,width=' + _width + ',height=' + _height
      window.open($(this).attr('href'), 'sharer', stringSpecs)
    })

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
  }, 1000)
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
  })

  $('.container-popup .btn-close').click(event => {
    window.setCookie('popup_closed', '1', 0.2) // 20s -> 0.000231481d // 2h24min -> 0.1d
    $('.container-popup').remove()
  })
})
