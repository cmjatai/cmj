window.ContainerFirst = function () {
  let first = $('.container-first')

  if (first.height() > window.innerHeight) {
    first.css('height', window.innerHeight)
    let btn = first.find('.btn').click(function () {
      this.parentElement.remove()
      first.css('height', '')
      first.removeClass('container-first')
    })
    if (btn.length === 0) {
      first.css('height', '')
      first.removeClass('container-first')
    }
  } else {
    first.removeClass('.container-first')
    first.css('height', '')
    first.find('.painel-corte').remove()
  }
}
