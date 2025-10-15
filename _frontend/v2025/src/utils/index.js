import $ from 'jquery'
import 'jquery-mask-plugin'

window.$ = $
window.jQuery = $

import './colormodes'
import './scrollheader'
// import './image_cropping'

(() => {
  'use strict'

  window.refreshMask = function () {
    $('.telefone').mask('(99) X9999-9999', {
      placeholder: '(__) _____-____',
      translation: {
        'X': {
          pattern: /[ 0-9]/,
          optional: false
        },
        '9': {
          pattern: /[0-9]/,
          optional: false
        }
      }
    })
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
    $('.formatted-natureza-despesa').mask('9.0.00.XX.XX', {
      placeholder: '9.9.99.XX.XX',
      translation: {
        'X': {
          pattern: /[X0-9]/,
          optional: true
        },
        '0': {
          pattern: /[0-9]/,
          optional: true
        },
        '9': {
          pattern: /[0-9]/,
          optional: false
        }
      }
    })
    $('.decimalinput:not(.decimal-precision)').mask('#.##0,00', {
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
  window.SetCookie = function (cookieName, cookieValue, nDays) {
    let today = new Date()
    let expire = new Date()
    if (nDays === null || nDays === 0) nDays = 1
    expire.setTime(today.getTime() + 3600000 * 24 * nDays)
    document.cookie = cookieName + '=' + escape(cookieValue) +
      ';expires=' + expire.toGMTString()
  }

  window.ReadCookie = function (cookieName) {
    let theCookie = ' ' + document.cookie
    let ind = theCookie.indexOf(' ' + cookieName + '=')
    if (ind === -1) ind = theCookie.indexOf(';' + cookieName + '=')
    if (ind === -1 || cookieName === '') return ''
    let ind1 = theCookie.indexOf(';', ind + 1)
    if (ind1 === -1) ind1 = theCookie.length
    return unescape(theCookie.substring(ind + cookieName.length + 2, ind1))
  }

  window.addEventListener('DOMContentLoaded', () => {

    window.refreshMask()

  })
})()

