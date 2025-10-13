window.Acessibilidade = function () {
  let VLibras = {
    storage: 'vlibras',
    currentState: null,
    check: checkVLibras,
    getState: getVLibrasState,
    setState: setVLibrasState,
    toogle: toogleVLibras,
    updateView: updateViewVLibras
  }

  window.toogleVLibras = function () {
    VLibras.toogle()
  }

  function checkVLibras () {
    this.updateView()
  }

  function getVLibrasState () {
    return localStorage.getItem(this.storage) === 'true'
  }

  function setVLibrasState (state) {
    localStorage.setItem(this.storage, '' + state)
    this.currentState = state
    this.updateView()
  }

  function updateViewVLibras () {
    let vw = document.querySelector('[vw]')
    if (this.currentState === null) {
      this.currentState = this.getState()
    }
    if (this.currentState) {
      vw.classList.remove('disabled')
      vw.classList.add('enabled')
    } else {
      vw.classList.remove('enabled')
      vw.classList.add('disabled')
    }
  }

  function toogleVLibras () {
    this.setState(!this.currentState)
  }

  let Contrast = {
    storage: 'contrastState',
    cssClass: 'contrast',
    currentState: null,
    check: checkContrast,
    getState: getContrastState,
    setState: setContrastState,
    toogle: toogleContrast,
    updateView: updateViewContrast
  }

  window.toogleContrast = function () {
    Contrast.toogle()
  }

  function checkContrast () {
    this.updateView()
  }

  function getContrastState () {
    return localStorage.getItem(this.storage) === 'true'
  }

  function setContrastState (state) {
    localStorage.setItem(this.storage, '' + state)
    this.currentState = state
    this.updateView()
  }

  function updateViewContrast () {
    let body = document.body
    if (this.currentState === null) {
      this.currentState = this.getState()
    }
    if (this.currentState) {
      body.classList.add(this.cssClass)
    } else {
      body.classList.remove(this.cssClass)
    }
  }

  function toogleContrast () {
    this.setState(!this.currentState)
  }

  let FontSizeZoom = {
    storage: 'fontSizeZoomState',
    getState: getFontSizeZoomState,
    setState: setFontSizeZoomState,
    currentState: 1.0,
    updateView: updateViewFontSizeZoom,
    toogle: execFontSizeZoom,
    check: checkFontSizeZoom
  }

  function checkFontSizeZoom () {
    this.updateView()
  }

  function execFontSizeZoom (action) {
    this.setState(action)
  }

  window.execFontSizeZoom = function (action) {
    FontSizeZoom.toogle(action)
  }

  function updateViewFontSizeZoom () {
    let body = document.body
    if (this.currentState === null) {
      this.currentState = 1.0
    }
    body.style.fontSize = `${this.getState()}rem`
  }

  function getFontSizeZoomState () {
    return localStorage.getItem(this.storage)
  }

  function setFontSizeZoomState (state) {
    let st = this.getState()
    if (st && state === 'up') {
      if (st < 1.8) {
        st *= 1.1
      }
    } else if (st && state === 'down') {
      if (st > 0.7) {
        st /= 1.1
      }
    } else {
      st = 1
    }
    localStorage.setItem(this.storage, st)
    this.currentState = state
    this.updateView()
  }

  let KeysAcessibilidade = {
    load: loadKeysAcessibilidade,
    keys: ''
  }

  function loadKeysAcessibilidade () {
    document.onkeydown = function isKeyPressed (event) {
      if ((KeysAcessibilidade.keys === 'AltGraph' || (event.ctrlKey && event.altKey)) && _.range(48, 58).includes(event.keyCode)) {
        KeysAcessibilidade.keys = ''
        switch (event.keyCode) {
          case 49: // 1
            window.location = '#main_content'
            break
          case 50: // 2
            window.location = '/'
            break
          case 51: // 3
            window.location = '/pesquisar/'
            break
          case 52: // 4
            window.location = '/mapa-do-site'
            break
          case 53: // 5
            window.execFontSizeZoom('down')
            break
          case 54: // 6
            window.execFontSizeZoom('up')
            break
          case 55: // 7
            window.toogleVLibras()
            break
          case 56: // 8
            window.toogleContrast()
            break
          case 57: // 9
            window.location = '/fale-conosco'
            break
          case 48: // 0
            window.location = '/acessibilidade'
            break
          default:
            break
        }
      }
      if (event.key === 'AltGraph') {
        KeysAcessibilidade.keys = 'AltGraph'
        setTimeout(() => {
          KeysAcessibilidade.keys = ''
        }, 5000)
      } else {
        KeysAcessibilidade.keys = ''
      }
    }
  }

  VLibras.check()
  Contrast.check()
  FontSizeZoom.check()
  KeysAcessibilidade.load()
}
