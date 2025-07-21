$(function () {
  // popups
  setTimeout(() => {
    $('.container-popup').css('display', 'flex')
  }, 500)

  $('#carousel-popup .carousel-item .click-item').click(event => {
    let pk = event.currentTarget.getAttribute('pk')
    let href = event.currentTarget.getAttribute('href')

    window.setCookie('popup_closed', '1', 0.006944444) // Caso o usuário clique em um popup, fica 10min sem mostrar popups
    window.setCookie(`popup_viewed_${pk}`, pk, 1.1) // Caso o usuário clique em um popup, fica 2h24min sem mostrar esse popup

    setTimeout(() => {
      document.location = `${href}?popup=1`
    }, 500)
  })

  $('.container-popup .btn-close').click(event => {
    window.setCookie('popup_closed', '1', 1.1) // 20s -> 0.000231481d // 2h24min -> 0.1d
    $('.container-popup').remove()
  })
})
