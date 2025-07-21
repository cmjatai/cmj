import './importlibs'

import './functions'

import { EyePassword } from './modules'

$(function () {
  // Verifica se o usuário já aceitou a LGPD
  if (!localStorage.portalcmj_primeiro_acesso) {
    document.getElementById('container-lgpd').style.display = 'block'
    document.getElementById('btn-lgpd-ciente').onclick = function () {
      document.getElementById('container-lgpd').style.display = 'none'
      localStorage.portalcmj_primeiro_acesso = 1
    }
  }

  setTimeout(function () {
    window.Acessibilidade()

    window.autorModal()
    window.refreshMask()
    window.refreshDatePicker()
    window.refreshSelectPicker()

    EyePassword()

    if (document.getElementById('texto-rico') !== null) {
      window.initTextRichEditor('#texto-rico')
    }

    $('[data-toggle="popover"]').popover({
      trigger: 'focus'
    })
  }, 500)
})
