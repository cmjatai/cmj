window.OptionalCustomFrontEnd = function () {
  // Adaptações opcionais de layout com a presença de JS.
  // Não implementar customizações que a funcionalidade que fique dependente.
  let instance
  if (!(this instanceof window.OptionalCustomFrontEnd)) {
    if (!instance) {
      instance = new window.OptionalCustomFrontEnd()
    }
    return instance
  }
  instance = this
  window.OptionalCustomFrontEnd = function () {
    return instance
  }
  instance.customCheckBoxAndRadio = function () {
    $('[type=radio], [type=checkbox]').each(function () {
      let _this = $(this)
      let _controls = _this.closest('.controls')
      _controls && _controls.find(':file').length === 0 && !_controls.hasClass('controls-radio-checkbox') && _controls.addClass('controls-radio-checkbox')
      _controls.find(':file').length > 0 && _controls.addClass('controls-file')
    })
  }
  instance.customCheckBoxAndRadioWithoutLabel = function () {
    $('[type=radio], [type=checkbox]').each(function () {
      let _this = $(this)
      let _label = _this.closest('label')

      if (_label.length) {
        return
      }

      if (this.id) {
        _label = $('label[for=' + this.id + ']')
      } else {
        _label = $('<label/>').insertBefore(this)
      }

      if (_label.length) {
        _label.addClass('checkbox-inline')
        _label.prepend(_this)
        _this.checkbox()
      }
    })
  }
  instance.init = function () {
    this.customCheckBoxAndRadio()
    this.customCheckBoxAndRadioWithoutLabel()
  }
  instance.init()
}
