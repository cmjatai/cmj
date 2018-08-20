
import jQuery from 'jquery'
window.$ = window.jQuery = jQuery

window.refreshDatePicker = function () {
  $.datepicker.setDefaults($.datepicker.regional['pt-BR'])
  $('.dateinput').datepicker()
}

window.refreshMask = function () {
  $('.telefone').mask('(99) 9999-9999', {placeholder: '(__) ____ -____'})
  $('.cpf').mask('000.000.000-00', {placeholder: '___.___.___-__'})
  $('.cep').mask('00000-000', {placeholder: '_____-___'})
  $('.rg').mask('0.000.000', {placeholder: '_.___.___'})
  $('.titulo_eleitor').mask('0000.0000.0000.0000', {placeholder: '____.____.____.____'})
  $('.dateinput').mask('00/00/0000', {placeholder: '__/__/____'})
  $('.hora').mask('00:00', {placeholder: 'hh:mm'})
  $('.hora_hms').mask('00:00:00', {placeholder: 'hh:mm:ss'})
  $('.datetimeinput').mask('00/00/0000 00:00:00', {placeholder: '__/__/____ hh:mm:ss'})
  $('.timeinput').mask('00:00', {placeholder: 'hh:mm'})
}
