import '@fortawesome/fontawesome-free/css/all.css'
// import '@fortawesome/fontawesome-free/js/all.js'

import 'bootstrap'
import 'bootstrap-select'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'
import 'webpack-jquery-ui/datepicker'
import 'jquery-ui/ui/i18n/datepicker-pt-BR'

import 'jquery-ui-themes/themes/pepper-grinder/jquery-ui.min.css'

import tinymce from 'tinymce/tinymce'
import './tinymce/lang/pt_BR.js'

import 'tinymce/themes/silver'
import 'tinymce/icons/default'
import 'tinymce/plugins/table'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/code'
import 'tinymce/plugins/link'
import 'tinymce/models/dom'

import 'jquery-mask-plugin'

import dateFormat from 'dateformat'

import * as moment from 'moment'
import 'moment/locale/pt-br'

// import './jquery_runner' // django app painel
import './image_cropping'

window.$ = $
window.jQuery = $

window.tinymce = tinymce
window.moment = moment
window.dateFormat = dateFormat
