(() => {
  'use strict'

  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
      // Verifica se o elemento existe antes de adicionar o evento
      if (!document.querySelector('#header-main')) {
        return
      }

      // Adiciona a classe 'header-scrolled' ao header quando a página é rolada
      const header = document.querySelector('#header-main')

      // Define uma função que verifica a posição do scroll e atualiza a classe do header
      function checkScroll() {
        if (window.scrollY > 0) {
          header.classList.add('header-scrolled')
        } else {
          header.classList.remove('header-scrolled')
        }
      }

      // Verifica imediatamente ao carregar a página
      checkScroll()

      // Adiciona o evento de scroll
      window.addEventListener('scroll', checkScroll)
    }, 2000)
  })
})()
