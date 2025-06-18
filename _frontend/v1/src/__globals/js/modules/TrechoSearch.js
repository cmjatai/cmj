window.TrechoSearch = function (opts) {
  $(function () {
    let ctsClear = $('body').children('.cts') // Container Trecho Search
    if (ctsClear.length > 0) {
      $(ctsClear).remove()
    }

    $("input[name='endereco']").each(function () {
      let input = $(this)
      let inputRow = $(input.closest('.row'))
      let cts = $('<div class="cts"/>')
      let qOld = input.val()
      let qNew = input.val()
      let intervalKeyPress = null
      input.after(cts)

      let ctsShow = function () {
        let rowPosition = inputRow[0].getBoundingClientRect()
        let inputPosition = input[0].getBoundingClientRect()
        cts.animate({
          'top': inputPosition.bottom,
          'left': inputPosition.left + 7,
          'right': rowPosition.right - rowPosition.width
        }, 400)
      }
      let ctsHidden = function () {
        cts.css('visibility', 'hidden')
      }

      $(window).resize(ctsHidden)
      $(window).scroll(ctsHidden)

      let zoomListeners = [ctsHidden]
      let lastWidth = 0
      let pollZoomFireEvent = function () {
        let widthNow = $(window).width()
        if (lastWidth === widthNow) return
        lastWidth = widthNow
        // Length changed, user must have zoomed, invoke listeners.
        for (let i = zoomListeners.length - 1; i >= 0; --i) {
          zoomListeners[i]()
        }
      }
      setInterval(pollZoomFireEvent, 300)

      let flagNewkeypress = false
      let flagGetRunAjax = false
      let keyUpEndereco = function () {
        if (qOld !== qNew) {
          qOld = qNew
          return
        }
        if (!flagNewkeypress) {
          return
        }
        flagNewkeypress = false

        if (flagGetRunAjax) {
          return
        }
        flagGetRunAjax = true

        let formData = {
          'q': qNew,
          'format': 'json'
        }
        $.get(opts.api_rest_list, formData).done(function (data) {
          cts.html('')
          ctsShow()
          cts.css('visibility', (data.results.length === 0 ? 'hidden' : 'visible'))

          $.each(data.results, function (index, itemData) {
            let its = $('<div class="its"/>') // Item de Trecho Search
            its.append(itemData.display)
            cts.append(its)

            its.on('click', function (event, setDataEndereco) {
              let pk = this.data
              let formData = {
                'format': 'json'
              }
              let url = opts.api_rest_retrieve
              url = url.replace('0', pk)
              $.get(url, formData, function (retrivieData) {
                $("input[name='trecho']").val(pk)
                if (setDataEndereco !== undefined && setDataEndereco) {
                  $("input[name='endereco']").attr('data', retrivieData.tipo_descricao + ' ' + retrivieData.logradouro_descricao)
                } else {
                  $("input[name='endereco']").val(retrivieData.tipo_descricao + ' ' + retrivieData.logradouro_descricao)
                }
                $("select[name='bairro']").val(retrivieData.bairro_id)
                $("input[name='cep']").val(retrivieData.cep[0])
                $("select[name='distrito']").val(retrivieData.distrito_id)
                $("select[name='regiao_municipal']").val(retrivieData.regiao_municipal_id)
                $("select[name='municipio']").val(retrivieData.municipio_id)
                $("select[name='uf']").val(retrivieData.uf)
              })
            })
            its[0].data = itemData.pk
          })
        }).always(function () {
          flagGetRunAjax = false
        })
      }
      input.on('keyup', function () {
        if (intervalKeyPress === null) {
          intervalKeyPress = setInterval(keyUpEndereco, 700)
        }
        flagNewkeypress = true
        qNew = input.val()
        if (qNew === qOld || qNew.length < 3) {
          cts.css('visibility', 'hidden')
        }
      }).on('blur', function () {
        let inputData = $(this).attr('data')
        if (inputData !== undefined && inputData !== '') {
          $(this).val(inputData)
        }

        setTimeout(function () {
          cts.css('visibility', 'hidden')
        }, 300)
      })
    })
  })
}
