import tinymce from 'tinymce/tinymce'
import './js/tinymce/lang/pt_BR.js'

import 'tinymce/themes/silver'
import 'tinymce/icons/default'
import 'tinymce/plugins/table'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/code'
import 'tinymce/plugins/link'
import 'tinymce/models/dom'

window.tinymce = tinymce

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

$(function () {
  setTimeout(function () {
    if (document.getElementById('texto-rico') !== null) {
      window.initTextRichEditor('#texto-rico')
    }
  }, 500)
})
