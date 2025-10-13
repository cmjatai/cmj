$(function () {
  setTimeout(function () {
    $('a[data-social-sharing]').click(function (event) {
      event.preventDefault()
      let socialNetwork = $(this).data('social-sharing')
      let _height, _width
      switch (socialNetwork) {
        case 'facebook': _height = 436; _width = 626; break
        case 'whatsapp': _height = 591; _width = 617; break
        case 'twitter': _height = 300; _width = 600; break
        case 'linkedin': _height = 576; _width = 570; break
        case 'copylink':
          var $temp = $('<input>')
          $('body').append($temp)
          $temp.val($(this).attr('href')).select()
          document.execCommand('copy')
          $temp.remove()
          return
        default: _height = 436; _width = 626; break
      }
      let leftPosition = (window.screen.width / 2) - ((_width / 2) + 10)
      let topPosition = (window.screen.height / 2) - ((_height / 2) + 50)
      let stringSpecs = 'left=' + leftPosition + ',top=' + topPosition + ',toolbar=0,status=0,width=' + _width + ',height=' + _height
      window.open($(this).attr('href'), 'sharer', stringSpecs)
    })
  }, 500)
})
