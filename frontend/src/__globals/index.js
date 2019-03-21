import '@fortawesome/fontawesome-free/css/all.css'
//import '@fortawesome/fontawesome-free/js/all.js'

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
//initTinymce
// import './2018/themes/dezembrolaranja/app.scss'
